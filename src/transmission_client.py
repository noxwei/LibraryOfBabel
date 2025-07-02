#!/usr/bin/env python3
"""
LibraryOfBabel: Transmission Client
u/TransmissionHacker Implementation

Handles communication with transmission-daemon for torrent management.
Features real-time progress monitoring and seeding compliance tracking.
"""

import json
import asyncio
import aiohttp
import base64
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class TorrentStatus:
    """Represents current status of a torrent in transmission"""
    hash_string: str
    id: int
    name: str
    status: int  # Transmission status codes
    status_text: str
    progress: float  # 0.0 to 1.0
    download_rate: int  # bytes/sec
    upload_rate: int  # bytes/sec
    eta: int  # seconds, -1 if unknown
    size_total: int  # bytes
    size_downloaded: int  # bytes
    size_uploaded: int  # bytes
    ratio: float
    peers_connected: int
    peers_total: int
    seeders: int
    leechers: int
    error: str
    download_dir: str
    files: List[Dict[str, Any]]
    date_added: int  # unix timestamp
    date_done: int  # unix timestamp

class TransmissionClient:
    """
    Transmission RPC Client for LibraryOfBabel
    
    Features:
    - Add torrents from files or magnet links
    - Real-time progress monitoring
    - Seeding compliance tracking
    - Automatic cleanup after seeding period
    """
    
    def __init__(self, host: str = "localhost", port: int = 9091, 
                 username: str = None, password: str = None):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_url = f"http://{host}:{port}/transmission/rpc"
        self.session_id = None
        self.session = None
        
        # Transmission status codes
        self.STATUS_CODES = {
            0: "stopped",
            1: "check_wait", 
            2: "check",
            3: "download_wait",
            4: "download",
            5: "seed_wait",
            6: "seed"
        }
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize_session()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def initialize_session(self):
        """Initialize aiohttp session and get transmission session ID"""
        auth = None
        if self.username and self.password:
            auth = aiohttp.BasicAuth(self.username, self.password)
            
        self.session = aiohttp.ClientSession(
            auth=auth,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Get session ID
        await self._get_session_id()
        
    async def _get_session_id(self):
        """Get transmission session ID required for RPC calls"""
        try:
            async with self.session.post(self.base_url, json={}) as response:
                if response.status == 409:
                    # Extract session ID from header
                    session_header = response.headers.get('X-Transmission-Session-Id')
                    if session_header:
                        self.session_id = session_header
                        logger.info("Transmission session ID obtained")
                    else:
                        raise Exception("Could not get session ID from transmission")
                else:
                    logger.warning(f"Unexpected response getting session ID: {response.status}")
        except Exception as e:
            logger.error(f"Failed to get transmission session ID: {e}")
            raise
            
    async def _rpc_call(self, method: str, arguments: Dict = None) -> Dict:
        """Make RPC call to transmission daemon"""
        if not self.session_id:
            await self._get_session_id()
            
        headers = {
            'X-Transmission-Session-Id': self.session_id,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'method': method,
            'arguments': arguments or {}
        }
        
        try:
            async with self.session.post(
                self.base_url, 
                headers=headers,
                json=payload
            ) as response:
                
                if response.status == 409:
                    # Session ID expired, get new one and retry
                    await self._get_session_id()
                    headers['X-Transmission-Session-Id'] = self.session_id
                    
                    async with self.session.post(
                        self.base_url,
                        headers=headers, 
                        json=payload
                    ) as retry_response:
                        result = await retry_response.json()
                        
                elif response.status == 200:
                    result = await response.json()
                    
                else:
                    raise Exception(f"RPC call failed with status {response.status}")
                    
                if result.get('result') != 'success':
                    raise Exception(f"RPC error: {result.get('result')}")
                    
                return result.get('arguments', {})
                
        except Exception as e:
            logger.error(f"RPC call {method} failed: {e}")
            raise
            
    async def add_torrent_file(self, torrent_file_path: str, download_dir: str = None) -> Optional[int]:
        """
        Add torrent from .torrent file
        
        Args:
            torrent_file_path: Path to .torrent file
            download_dir: Directory to download files to
            
        Returns:
            Torrent ID if successful, None if failed
        """
        try:
            # Read and encode torrent file
            with open(torrent_file_path, 'rb') as f:
                torrent_data = f.read()
                
            encoded_data = base64.b64encode(torrent_data).decode('utf-8')
            
            arguments = {
                'metainfo': encoded_data
            }
            
            if download_dir:
                arguments['download-dir'] = download_dir
                
            result = await self._rpc_call('torrent-add', arguments)
            
            # Check if torrent was added or already exists
            torrent_added = result.get('torrent-added')
            torrent_duplicate = result.get('torrent-duplicate')
            
            if torrent_added:
                torrent_id = torrent_added['id']
                torrent_name = torrent_added['name']
                logger.info(f"Torrent added: {torrent_name} (ID: {torrent_id})")
                return torrent_id
                
            elif torrent_duplicate:
                torrent_id = torrent_duplicate['id'] 
                torrent_name = torrent_duplicate['name']
                logger.info(f"Torrent already exists: {torrent_name} (ID: {torrent_id})")
                return torrent_id
                
            else:
                logger.error("Unknown response from torrent-add")
                return None
                
        except Exception as e:
            logger.error(f"Failed to add torrent {torrent_file_path}: {e}")
            return None
            
    async def get_torrent_status(self, torrent_id: int) -> Optional[TorrentStatus]:
        """Get detailed status for specific torrent"""
        try:
            arguments = {
                'ids': [torrent_id],
                'fields': [
                    'id', 'name', 'hashString', 'status', 'percentDone',
                    'rateDownload', 'rateUpload', 'eta', 'totalSize',
                    'downloadedEver', 'uploadedEver', 'uploadRatio',
                    'peersConnected', 'peersGettingFromUs', 'peersSendingToUs',
                    'seedRatioLimit', 'error', 'errorString', 'downloadDir',
                    'files', 'addedDate', 'doneDate'
                ]
            }
            
            result = await self._rpc_call('torrent-get', arguments)
            torrents = result.get('torrents', [])
            
            if not torrents:
                return None
                
            t = torrents[0]
            
            status = TorrentStatus(
                hash_string=t.get('hashString', ''),
                id=t.get('id', 0),
                name=t.get('name', ''),
                status=t.get('status', 0),
                status_text=self.STATUS_CODES.get(t.get('status', 0), 'unknown'),
                progress=t.get('percentDone', 0.0),
                download_rate=t.get('rateDownload', 0),
                upload_rate=t.get('rateUpload', 0),
                eta=t.get('eta', -1),
                size_total=t.get('totalSize', 0),
                size_downloaded=t.get('downloadedEver', 0),
                size_uploaded=t.get('uploadedEver', 0),
                ratio=t.get('uploadRatio', 0.0),
                peers_connected=t.get('peersConnected', 0),
                peers_total=t.get('peersSendingToUs', 0) + t.get('peersGettingFromUs', 0),
                seeders=t.get('peersSendingToUs', 0),
                leechers=t.get('peersGettingFromUs', 0),
                error=t.get('errorString', ''),
                download_dir=t.get('downloadDir', ''),
                files=t.get('files', []),
                date_added=t.get('addedDate', 0),
                date_done=t.get('doneDate', 0)
            )
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get torrent status {torrent_id}: {e}")
            return None
            
    async def monitor_torrent_progress(self, torrent_id: int, 
                                     progress_callback=None, 
                                     check_interval: float = 5.0) -> TorrentStatus:
        """
        Monitor torrent progress until completion
        
        Args:
            torrent_id: Torrent to monitor
            progress_callback: Called with TorrentStatus updates
            check_interval: How often to check status (seconds)
            
        Returns:
            Final TorrentStatus when complete
        """
        logger.info(f"Starting progress monitoring for torrent {torrent_id}")
        
        while True:
            status = await self.get_torrent_status(torrent_id)
            
            if not status:
                logger.error(f"Lost track of torrent {torrent_id}")
                break
                
            # Call progress callback if provided
            if progress_callback:
                await progress_callback(status)
                
            # Check if download is complete
            if status.progress >= 1.0 and status.status in [5, 6]:  # seed_wait or seed
                logger.info(f"Download complete: {status.name}")
                return status
                
            # Check for errors
            if status.error:
                logger.error(f"Torrent error: {status.error}")
                break
                
            await asyncio.sleep(check_interval)
            
        return status
        
    async def remove_torrent(self, torrent_id: int, delete_files: bool = False) -> bool:
        """Remove torrent from transmission"""
        try:
            arguments = {
                'ids': [torrent_id],
                'delete-local-data': delete_files
            }
            
            await self._rpc_call('torrent-remove', arguments)
            logger.info(f"Torrent {torrent_id} removed (delete_files={delete_files})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove torrent {torrent_id}: {e}")
            return False
            
    async def get_session_stats(self) -> Dict:
        """Get transmission session statistics"""
        try:
            result = await self._rpc_call('session-stats')
            return result
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}
            
    def format_bytes(self, bytes_value: int) -> str:
        """Format bytes as human readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} PB"
        
    def format_time(self, seconds: int) -> str:
        """Format seconds as human readable time"""
        if seconds < 0:
            return "Unknown"
        elif seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

# Test function
async def test_transmission_client():
    """Test transmission client connectivity"""
    async with TransmissionClient() as client:
        stats = await client.get_session_stats()
        print(f"Transmission stats: {json.dumps(stats, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_transmission_client())