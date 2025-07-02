#!/usr/bin/env python3
"""
LibraryOfBabel: Download API Endpoints
u/TransmissionHacker Implementation

REST API endpoints for frontend integration with the download pipeline.
Provides real-time status updates and download management.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import asyncpg

from ..download_pipeline import DownloadPipeline

logger = logging.getLogger(__name__)

class DownloadAPI:
    """REST API for download pipeline management"""
    
    def __init__(self, db_config: Dict, transmission_config: Dict = None):
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for frontend
        
        self.db_config = db_config
        self.transmission_config = transmission_config or {}
        self.pipeline = None
        
        # Setup routes
        self._setup_routes()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
    def _setup_routes(self):
        """Setup all API routes"""
        
        @self.app.route('/api/download/search-start', methods=['POST'])
        async def start_download():
            """Start new download request"""
            try:
                data = request.get_json()
                
                if not data or not data.get('title') or not data.get('author'):
                    return jsonify({
                        'error': 'title and author are required'
                    }), 400
                    
                title = data['title'].strip()
                author = data['author'].strip()
                
                # Get client info
                user_agent = request.headers.get('User-Agent')
                ip_address = request.remote_addr
                
                if not self.pipeline:
                    await self._initialize_pipeline()
                    
                request_id = await self.pipeline.start_download(
                    title, author, user_agent, ip_address
                )
                
                return jsonify({
                    'request_id': request_id,
                    'status': 'initiated',
                    'title': title,
                    'author': author,
                    'message': 'Download request created successfully'
                })
                
            except Exception as e:
                logger.error(f"Failed to start download: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e)
                }), 500
                
        @self.app.route('/api/download/status/<int:request_id>', methods=['GET'])
        async def get_download_status(request_id: int):
            """Get status of specific download request"""
            try:
                if not self.pipeline:
                    await self._initialize_pipeline()
                    
                status = await self.pipeline.get_download_status(request_id)
                
                if not status:
                    return jsonify({
                        'error': 'Download request not found'
                    }), 404
                    
                # Format response
                response = {
                    'request_id': status['request_id'],
                    'title': status.get('book_title'),
                    'author': status.get('book_author'),
                    'status': status['status'],
                    'progress': float(status.get('progress', 0)),
                    'download_speed': status.get('download_speed'),
                    'upload_speed': status.get('upload_speed'),
                    'eta': status.get('eta'),
                    'file_size': status.get('file_size'),
                    'file_path': status.get('file_path'),
                    'created_at': status['created_at'].isoformat() if status.get('created_at') else None,
                    'completed_at': status['completed_at'].isoformat() if status.get('completed_at') else None,
                    'error_message': status.get('error_message')
                }
                
                # Add MAM search results if available
                if status.get('mam_search_results'):
                    try:
                        response['mam_results'] = json.loads(status['mam_search_results'])
                    except:
                        pass
                        
                return jsonify(response)
                
            except Exception as e:
                logger.error(f"Failed to get download status: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e)
                }), 500
                
        @self.app.route('/api/download/history', methods=['GET'])
        async def get_download_history():
            """Get download history with optional filtering"""
            try:
                # Query parameters
                status_filter = request.args.get('status')
                limit = int(request.args.get('limit', 50))
                offset = int(request.args.get('offset', 0))
                
                if not self.pipeline:
                    await self._initialize_pipeline()
                    
                async with self.pipeline.db_pool.acquire() as conn:
                    
                    # Build query
                    where_clause = ""
                    params = []
                    param_count = 0
                    
                    if status_filter:
                        param_count += 1
                        where_clause = f"WHERE status = ${param_count}"
                        params.append(status_filter)
                        
                    param_count += 1
                    limit_param = param_count
                    param_count += 1
                    offset_param = param_count
                    
                    query = f"""
                        SELECT request_id, book_title, book_author, status, 
                               progress, created_at, completed_at, error_message
                        FROM download_requests 
                        {where_clause}
                        ORDER BY created_at DESC 
                        LIMIT ${limit_param} OFFSET ${offset_param}
                    """
                    
                    params.extend([limit, offset])
                    rows = await conn.fetch(query, *params)
                    
                    # Format response
                    downloads = []
                    for row in rows:
                        downloads.append({
                            'request_id': row['request_id'],
                            'title': row['book_title'],
                            'author': row['book_author'],
                            'status': row['status'],
                            'progress': float(row['progress'] or 0),
                            'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                            'completed_at': row['completed_at'].isoformat() if row['completed_at'] else None,
                            'error_message': row['error_message']
                        })
                        
                    return jsonify({
                        'downloads': downloads,
                        'total': len(downloads),
                        'limit': limit,
                        'offset': offset
                    })
                    
            except Exception as e:
                logger.error(f"Failed to get download history: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e)
                }), 500
                
        @self.app.route('/api/download/active', methods=['GET'])
        async def get_active_downloads():
            """Get all currently active downloads"""
            try:
                if not self.pipeline:
                    await self._initialize_pipeline()
                    
                active_downloads = await self.pipeline.list_active_downloads()
                
                # Format response
                formatted_downloads = []
                for download in active_downloads:
                    formatted_downloads.append({
                        'request_id': download['request_id'],
                        'title': download.get('book_title'),
                        'author': download.get('book_author'),
                        'status': download['status'],
                        'progress': float(download.get('progress', 0)),
                        'download_speed': download.get('download_speed'),
                        'eta': download.get('eta'),
                        'created_at': download['created_at'].isoformat() if download.get('created_at') else None
                    })
                    
                return jsonify({
                    'active_downloads': formatted_downloads,
                    'count': len(formatted_downloads)
                })
                
            except Exception as e:
                logger.error(f"Failed to get active downloads: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e)
                }), 500
                
        @self.app.route('/api/download/cancel/<int:request_id>', methods=['DELETE'])
        async def cancel_download(request_id: int):
            """Cancel active download"""
            try:
                if not self.pipeline:
                    await self._initialize_pipeline()
                    
                # Update status to cancelled
                async with self.pipeline.db_pool.acquire() as conn:
                    result = await conn.execute(
                        """
                        UPDATE download_requests 
                        SET status = 'cancelled'
                        WHERE request_id = $1 AND status IN ('searching', 'found', 'downloading')
                        """,
                        request_id
                    )
                    
                    if result == 'UPDATE 0':
                        return jsonify({
                            'error': 'Download not found or cannot be cancelled'
                        }), 404
                        
                # TODO: Remove from transmission if it's there
                        
                return jsonify({
                    'message': 'Download cancelled successfully',
                    'request_id': request_id
                })
                
            except Exception as e:
                logger.error(f"Failed to cancel download: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e)
                }), 500
                
        @self.app.route('/api/download/retry/<int:request_id>', methods=['POST'])
        async def retry_download(request_id: int):
            """Retry failed download"""
            try:
                if not self.pipeline:
                    await self._initialize_pipeline()
                    
                # Get original request
                status = await self.pipeline.get_download_status(request_id)
                
                if not status:
                    return jsonify({
                        'error': 'Download request not found'
                    }), 404
                    
                if status['status'] != 'failed':
                    return jsonify({
                        'error': 'Can only retry failed downloads'
                    }), 400
                    
                # Reset status and retry
                async with self.pipeline.db_pool.acquire() as conn:
                    await conn.execute(
                        """
                        UPDATE download_requests 
                        SET status = 'initiated', error_message = NULL, 
                            retry_count = retry_count + 1
                        WHERE request_id = $1
                        """,
                        request_id
                    )
                    
                # Restart download process
                asyncio.create_task(self.pipeline._process_download(
                    request_id, status['book_title'], status['book_author']
                ))
                
                return jsonify({
                    'message': 'Download retry initiated',
                    'request_id': request_id
                })
                
            except Exception as e:
                logger.error(f"Failed to retry download: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e)
                }), 500
                
        @self.app.route('/api/download/stats', methods=['GET'])
        async def get_download_stats():
            """Get download pipeline statistics"""
            try:
                if not self.pipeline:
                    await self._initialize_pipeline()
                    
                async with self.pipeline.db_pool.acquire() as conn:
                    # Get status counts
                    status_counts = await conn.fetch(
                        """
                        SELECT status, COUNT(*) as count
                        FROM download_requests
                        GROUP BY status
                        """
                    )
                    
                    # Get recent activity
                    recent_downloads = await conn.fetchval(
                        """
                        SELECT COUNT(*)
                        FROM download_requests
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                        """
                    )
                    
                    # Get success rate
                    success_rate = await conn.fetchrow(
                        """
                        SELECT 
                            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                            COUNT(*) as total,
                            ROUND(
                                COUNT(CASE WHEN status = 'completed' THEN 1 END) * 100.0 / 
                                NULLIF(COUNT(*), 0), 2
                            ) as success_rate
                        FROM download_requests
                        WHERE status IN ('completed', 'failed')
                        """
                    )
                    
                return jsonify({
                    'status_counts': {row['status']: row['count'] for row in status_counts},
                    'recent_downloads_24h': recent_downloads,
                    'success_rate': float(success_rate['success_rate'] or 0),
                    'total_requests': sum(row['count'] for row in status_counts)
                })
                
            except Exception as e:
                logger.error(f"Failed to get download stats: {e}")
                return jsonify({
                    'error': 'Internal server error',
                    'details': str(e)
                }), 500
                
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'service': 'LibraryOfBabel Download API',
                'timestamp': datetime.utcnow().isoformat()
            })
            
    async def _initialize_pipeline(self):
        """Initialize download pipeline"""
        if not self.pipeline:
            self.pipeline = DownloadPipeline(self.db_config, self.transmission_config)
            await self.pipeline.initialize()
            
    async def cleanup(self):
        """Cleanup resources"""
        if self.pipeline:
            await self.pipeline.cleanup()
            
    def run(self, host='localhost', port=5001, debug=False):
        """Run the API server"""
        try:
            self.app.run(host=host, port=port, debug=debug)
        finally:
            # Cleanup on shutdown
            if self.pipeline:
                asyncio.run(self.cleanup())

# Configuration and startup
def create_app():
    """Create and configure the Flask app"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'libraryofbabel'),
        'user': os.getenv('DB_USER', 'libraryofbabel_user'),
        'password': os.getenv('DB_PASSWORD', 'your_password')
    }
    
    # Transmission configuration
    transmission_config = {
        'host': os.getenv('TRANSMISSION_HOST', 'localhost'),
        'port': int(os.getenv('TRANSMISSION_PORT', 9091)),
        'username': os.getenv('TRANSMISSION_USER'),
        'password': os.getenv('TRANSMISSION_PASSWORD')
    }
    
    api = DownloadAPI(db_config, transmission_config)
    return api.app

if __name__ == '__main__':
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)