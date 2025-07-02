#!/usr/bin/env python3
"""
LibraryOfBabel: Download Pipeline Orchestrator  
u/TransmissionHacker Implementation

Main orchestrator that coordinates MAM search, transmission download, 
and database logging for the complete ebook acquisition pipeline.
"""

import asyncio
import asyncpg
import json
import os
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable
import logging

from .mam_api_client import MAMAPIClient, MAMTorrent
from .transmission_client import TransmissionClient, TorrentStatus

logger = logging.getLogger(__name__)

class DownloadPipeline:
    """
    Complete ebook download pipeline orchestrator
    
    Workflow:
    1. Receive download request (title, author)
    2. Search MAM for matching torrents
    3. Select best match based on confidence
    4. Download .torrent file
    5. Add to transmission
    6. Monitor progress and log to database
    7. Handle completion and seeding compliance
    """
    
    def __init__(self, 
                 db_config: Dict,
                 transmission_config: Dict = None,
                 download_dir: str = "./ebooks/downloads",
                 torrent_dir: str = "./ebooks/torrents"):
        
        self.db_config = db_config
        self.transmission_config = transmission_config or {}
        self.download_dir = Path(download_dir)
        self.torrent_dir = Path(torrent_dir)
        
        # Ensure directories exist
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.torrent_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_pool = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.db_pool = await asyncpg.create_pool(**self.db_config)
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
            
    async def cleanup(self):
        """Cleanup resources"""
        if self.db_pool:
            await self.db_pool.close()
            
    async def __aenter__(self):
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
        
    async def start_download(self, 
                           title: str, 
                           author: str,
                           user_agent: str = None,
                           ip_address: str = None) -> int:
        """
        Start download process for book
        
        Args:
            title: Book title to search for
            author: Author name
            user_agent: User agent from request
            ip_address: IP address from request
            
        Returns:
            request_id for tracking the download
        """
        
        # Create download request record
        async with self.db_pool.acquire() as conn:
            request_id = await conn.fetchval(
                """
                INSERT INTO download_requests (
                    search_query, book_title, book_author, 
                    user_agent, ip_address, status
                ) VALUES ($1, $2, $3, $4, $5, 'initiated')
                RETURNING request_id
                """,
                f"{title} {author}", title, author, user_agent, ip_address
            )
            
        logger.info(f"Created download request {request_id} for '{title}' by {author}")
        
        # Start async download process
        asyncio.create_task(self._process_download(request_id, title, author))
        
        return request_id
        
    async def _process_download(self, request_id: int, title: str, author: str):
        """Background task to handle the complete download process"""
        
        try:
            # Phase 1: Search MAM
            await self._update_status(request_id, 'searching')
            torrents = await self._search_mam(request_id, title, author)
            
            if not torrents:
                await self._update_status(request_id, 'failed', 
                                        error_message="No torrents found on MAM")
                return
                
            # Phase 2: Download torrent file
            best_torrent = torrents[0]  # Highest confidence
            torrent_file_path = await self._download_torrent_file(request_id, best_torrent)
            
            if not torrent_file_path:
                await self._update_status(request_id, 'failed',
                                        error_message="Failed to download .torrent file")
                return
                
            # Phase 3: Add to transmission
            await self._update_status(request_id, 'found')
            transmission_id = await self._add_to_transmission(request_id, torrent_file_path)
            
            if not transmission_id:
                await self._update_status(request_id, 'failed',
                                        error_message="Failed to add torrent to transmission")
                return
                
            # Phase 4: Monitor download progress
            await self._update_status(request_id, 'downloading')
            final_status = await self._monitor_download(request_id, transmission_id)
            
            if final_status and final_status.progress >= 1.0:
                await self._update_status(request_id, 'completed')
                
                # Phase 5: Setup seeding compliance
                await self._setup_seeding_compliance(request_id, final_status)
                
                # Phase 6: Process downloaded ebook
                await self._process_completed_ebook(request_id, final_status)
                
            else:
                await self._update_status(request_id, 'failed',
                                        error_message="Download did not complete successfully")
                
        except Exception as e:
            logger.error(f"Download process failed for request {request_id}: {e}")
            await self._update_status(request_id, 'failed', 
                                    error_message=str(e))
            
    async def _search_mam(self, request_id: int, title: str, author: str) -> List[MAMTorrent]:
        """Search MAM for torrents"""
        try:
            async with MAMAPIClient() as mam_client:
                torrents = await mam_client.search_ebooks(title, author)
                
                # Log search results to database
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE download_requests 
                        SET mam_search_results = $1, searched_at = NOW()
                        WHERE request_id = $2
                        """,
                        json.dumps([{
                            'id': t.id,
                            'title': t.title,
                            'author': t.author,
                            'size': t.size,
                            'confidence_score': t.confidence_score,
                            'seeders': t.seeders,
                            'leechers': t.leechers
                        } for t in torrents]),
                        request_id
                    )
                    
                logger.info(f"Found {len(torrents)} torrents for request {request_id}")
                return torrents
                
        except Exception as e:
            logger.error(f"MAM search failed for request {request_id}: {e}")
            return []
            
    async def _download_torrent_file(self, request_id: int, torrent: MAMTorrent) -> Optional[str]:
        """Download .torrent file"""
        try:
            torrent_file_path = self.torrent_dir / f"{request_id}_{torrent.id}.torrent"
            
            async with MAMAPIClient() as mam_client:
                success = await mam_client.download_torrent_file(
                    torrent, str(torrent_file_path)
                )
                
                if success:
                    # Update database with torrent info
                    async with self.db_pool.acquire() as conn:
                        await conn.execute(
                            """
                            UPDATE download_requests 
                            SET mam_torrent_id = $1, torrent_url = $2
                            WHERE request_id = $3
                            """,
                            torrent.id, torrent.download_url, request_id
                        )
                        
                    return str(torrent_file_path)
                    
            return None
            
        except Exception as e:
            logger.error(f"Torrent download failed for request {request_id}: {e}")
            return None
            
    async def _add_to_transmission(self, request_id: int, torrent_file_path: str) -> Optional[int]:
        """Add torrent to transmission"""
        try:
            async with TransmissionClient(**self.transmission_config) as transmission:
                transmission_id = await transmission.add_torrent_file(
                    torrent_file_path, str(self.download_dir)
                )
                
                if transmission_id:
                    # Get torrent hash for tracking
                    status = await transmission.get_torrent_status(transmission_id)
                    
                    if status:
                        async with self.db_pool.acquire() as conn:
                            await conn.execute(
                                """
                                UPDATE download_requests 
                                SET transmission_id = $1, transmission_hash = $2, started_at = NOW()
                                WHERE request_id = $3
                                """,
                                transmission_id, status.hash_string, request_id
                            )
                            
                        logger.info(f"Added torrent to transmission: ID {transmission_id}")
                        return transmission_id
                        
            return None
            
        except Exception as e:
            logger.error(f"Failed to add torrent to transmission for request {request_id}: {e}")
            return None
            
    async def _monitor_download(self, request_id: int, transmission_id: int) -> Optional[TorrentStatus]:
        """Monitor download progress"""
        try:
            async with TransmissionClient(**self.transmission_config) as transmission:
                
                async def progress_callback(status: TorrentStatus):
                    """Update database with progress"""
                    await self._update_progress(request_id, status)
                    
                final_status = await transmission.monitor_torrent_progress(
                    transmission_id, 
                    progress_callback=progress_callback,
                    check_interval=10.0
                )
                
                return final_status
                
        except Exception as e:
            logger.error(f"Download monitoring failed for request {request_id}: {e}")
            return None
            
    async def _update_progress(self, request_id: int, status: TorrentStatus):
        """Update download progress in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE download_requests 
                    SET progress = $1, download_speed = $2, upload_speed = $3, 
                        eta = $4, file_size = $5
                    WHERE request_id = $6
                    """,
                    status.progress * 100,  # Convert to percentage
                    f"{status.download_rate} B/s" if status.download_rate > 0 else None,
                    f"{status.upload_rate} B/s" if status.upload_rate > 0 else None,
                    f"{status.eta}s" if status.eta > 0 else None,
                    status.size_total,
                    request_id
                )
                
        except Exception as e:
            logger.error(f"Failed to update progress for request {request_id}: {e}")
            
    async def _update_status(self, request_id: int, status: str, error_message: str = None):
        """Update request status"""
        try:
            async with self.db_pool.acquire() as conn:
                if error_message:
                    await conn.execute(
                        """
                        UPDATE download_requests 
                        SET status = $1, error_message = $2
                        WHERE request_id = $3
                        """,
                        status, error_message, request_id
                    )
                else:
                    await conn.execute(
                        """
                        UPDATE download_requests 
                        SET status = $1
                        WHERE request_id = $2
                        """,
                        status, request_id
                    )
                    
                    # Set completion timestamp if completed
                    if status == 'completed':
                        await conn.execute(
                            """
                            UPDATE download_requests 
                            SET completed_at = NOW()
                            WHERE request_id = $1
                            """,
                            request_id
                        )
                        
            logger.info(f"Updated request {request_id} status to: {status}")
            
        except Exception as e:
            logger.error(f"Failed to update status for request {request_id}: {e}")
            
    async def _setup_seeding_compliance(self, request_id: int, status: TorrentStatus):
        """Setup seeding compliance tracking"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO seeding_compliance 
                    (request_id, transmission_hash, current_ratio, total_uploaded)
                    VALUES ($1, $2, $3, $4)
                    """,
                    request_id, status.hash_string, status.ratio, status.size_uploaded
                )
                
            logger.info(f"Setup seeding compliance tracking for request {request_id}")
            
        except Exception as e:
            logger.error(f"Failed to setup seeding compliance for request {request_id}: {e}")
            
    async def _process_completed_ebook(self, request_id: int, status: TorrentStatus):
        """Process completed ebook download"""
        try:
            # Find downloaded files
            download_path = Path(status.download_dir) / status.name
            ebook_files = []
            
            if download_path.is_file():
                ebook_files = [download_path]
            elif download_path.is_dir():
                # Find ebook files in directory
                for ext in ['.epub', '.pdf', '.mobi', '.azw3']:
                    ebook_files.extend(download_path.glob(f"**/*{ext}"))
                    
            if ebook_files:
                # Update database with file path
                async with self.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE download_requests 
                        SET file_path = $1, file_format = $2
                        WHERE request_id = $3
                        """,
                        str(ebook_files[0]),
                        ebook_files[0].suffix.lower(),
                        request_id
                    )
                    
                logger.info(f"Completed ebook ready for processing: {ebook_files[0]}")
                
                # TODO: Trigger EPUB processing pipeline here
                # await self._trigger_epub_processing(ebook_files[0])
                
            else:
                logger.warning(f"No ebook files found for completed download {request_id}")
                
        except Exception as e:
            logger.error(f"Failed to process completed ebook for request {request_id}: {e}")
            
    async def get_download_status(self, request_id: int) -> Optional[Dict]:
        """Get current status of download request"""
        try:
            async with self.db_pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    SELECT * FROM download_requests WHERE request_id = $1
                    """,
                    request_id
                )
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Failed to get download status for request {request_id}: {e}")
            return None
            
    async def list_active_downloads(self) -> List[Dict]:
        """List all active downloads"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT * FROM download_requests 
                    WHERE status IN ('searching', 'found', 'downloading', 'seeding')
                    ORDER BY created_at DESC
                    """
                )
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to list active downloads: {e}")
            return []

# Test function
async def test_download_pipeline():
    """Test the download pipeline with sample book"""
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'libraryofbabel',
        'user': 'libraryofbabel_user',
        'password': 'your_password'
    }
    
    async with DownloadPipeline(db_config) as pipeline:
        request_id = await pipeline.start_download("14 Miles", "AJ Gibson")
        print(f"Started download request: {request_id}")
        
        # Monitor for a bit
        for i in range(10):
            await asyncio.sleep(5)
            status = await pipeline.get_download_status(request_id)
            print(f"Status: {status['status']} - Progress: {status.get('progress', 0)}%")
            
            if status['status'] in ['completed', 'failed']:
                break

if __name__ == "__main__":
    asyncio.run(test_download_pipeline())