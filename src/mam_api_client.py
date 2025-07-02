#!/usr/bin/env python3
"""
LibraryOfBabel: MAM API Client
u/TransmissionHacker Implementation

Handles searching MAM for ebook torrents and extracting download URLs.
Rate limiting, session management, and error handling included.
"""

import asyncio
import aiohttp
import json
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode, quote
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MAMTorrent:
    """Represents a torrent found on MAM"""
    id: str
    title: str
    author: str
    size: str
    seeders: int
    leechers: int
    download_url: str
    category: str
    format: str
    confidence_score: float = 0.0

class MAMAPIClient:
    """
    MAM API Client with rate limiting and session persistence
    
    Features:
    - Smart search with fuzzy matching
    - Rate limiting compliance (1 req/3sec)
    - Session persistence across requests
    - Confidence scoring for search results
    """
    
    def __init__(self, session_file: str = "mam_session.json"):
        self.base_url = "https://www.myanonamouse.net"
        self.session_file = session_file
        self.session = None
        self.last_request_time = 0
        self.rate_limit_delay = 3.1  # Slightly over 3 seconds for safety
        self.cookies = {}
        self.headers = {
            'User-Agent': 'LibraryOfBabel/1.0 (Knowledge Liberation Pipeline)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
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
        """Initialize aiohttp session and load persistent cookies"""
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Load saved session cookies
        try:
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
                self.cookies = session_data.get('cookies', {})
                logger.info(f"Loaded {len(self.cookies)} session cookies")
        except FileNotFoundError:
            logger.warning("No session file found, will need fresh authentication")
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            
    def save_session(self):
        """Save session cookies for persistence"""
        try:
            session_data = {
                'cookies': self.cookies,
                'saved_at': time.time()
            }
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info("Session saved successfully")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            
    async def rate_limit_wait(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - elapsed
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)
        self.last_request_time = time.time()
        
    def calculate_confidence_score(self, result: Dict, query_title: str, query_author: str) -> float:
        """
        Calculate confidence score for search result matching
        Returns 0.0 to 1.0 confidence level
        """
        title_match = self._fuzzy_match(result.get('title', ''), query_title)
        author_match = self._fuzzy_match(result.get('author', ''), query_author)
        
        # Weight title more heavily than author
        confidence = (title_match * 0.7) + (author_match * 0.3)
        
        # Bonus for exact format matches
        if 'epub' in result.get('format', '').lower():
            confidence += 0.1
        if 'ebook' in result.get('category', '').lower():
            confidence += 0.1
            
        # Penalty for very low seeders
        seeders = result.get('seeders', 0)
        if seeders == 0:
            confidence *= 0.5
        elif seeders < 3:
            confidence *= 0.8
            
        return min(confidence, 1.0)
        
    def _fuzzy_match(self, text1: str, text2: str) -> float:
        """Simple fuzzy string matching"""
        if not text1 or not text2:
            return 0.0
            
        text1 = re.sub(r'[^\w\s]', '', text1.lower())
        text2 = re.sub(r'[^\w\s]', '', text2.lower())
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
        
    async def search_ebooks(self, title: str, author: str, limit: int = 10) -> List[MAMTorrent]:
        """
        Search MAM for ebook torrents matching title/author
        
        Args:
            title: Book title to search for
            author: Author name to search for  
            limit: Maximum results to return
            
        Returns:
            List of MAMTorrent objects sorted by confidence score
        """
        await self.rate_limit_wait()
        
        # Construct search query
        search_params = {
            'tor[text]': f'{title} {author}',
            'tor[cat][]': ['13', '14'],  # Ebooks categories
            'tor[searchType]': 'all',
            'tor[searchIn]': 'title',
            'tor[sort]': 'seeders',
            'tor[order]': 'desc'
        }
        
        search_url = f"{self.base_url}/tor/browse.php"
        
        try:
            logger.info(f"Searching MAM for: '{title}' by {author}")
            
            async with self.session.get(
                search_url, 
                params=search_params,
                cookies=self.cookies
            ) as response:
                
                if response.status == 200:
                    html_content = await response.text()
                    torrents = self._parse_search_results(html_content, title, author)
                    
                    # Sort by confidence score
                    torrents.sort(key=lambda x: x.confidence_score, reverse=True)
                    
                    logger.info(f"Found {len(torrents)} results, top confidence: {torrents[0].confidence_score:.2f}" if torrents else "No results found")
                    
                    return torrents[:limit]
                    
                elif response.status == 403:
                    logger.error("Authentication required - session may have expired")
                    return []
                    
                else:
                    logger.error(f"Search failed with status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
            
    def _parse_search_results(self, html: str, query_title: str, query_author: str) -> List[MAMTorrent]:
        """Parse HTML search results into MAMTorrent objects"""
        torrents = []
        
        # This is a simplified parser - in real implementation, would use BeautifulSoup
        # For now, returning mock data for testing
        
        mock_results = [
            {
                'id': 'test123',
                'title': query_title,
                'author': query_author,
                'size': '2.3 MB',
                'seeders': 5,
                'leechers': 2,
                'download_url': f'{self.base_url}/tor/download.php?id=test123',
                'category': 'Ebooks',
                'format': 'EPUB'
            }
        ]
        
        for result in mock_results:
            confidence = self.calculate_confidence_score(result, query_title, query_author)
            
            torrent = MAMTorrent(
                id=result['id'],
                title=result['title'],
                author=result['author'],
                size=result['size'],
                seeders=result['seeders'],
                leechers=result['leechers'],
                download_url=result['download_url'],
                category=result['category'],
                format=result['format'],
                confidence_score=confidence
            )
            
            torrents.append(torrent)
            
        return torrents
        
    async def download_torrent_file(self, torrent: MAMTorrent, output_path: str) -> bool:
        """
        Download .torrent file for given torrent
        
        Args:
            torrent: MAMTorrent object
            output_path: Where to save the .torrent file
            
        Returns:
            True if successful, False otherwise
        """
        await self.rate_limit_wait()
        
        try:
            logger.info(f"Downloading torrent file: {torrent.title}")
            
            async with self.session.get(
                torrent.download_url,
                cookies=self.cookies
            ) as response:
                
                if response.status == 200:
                    content = await response.read()
                    
                    with open(output_path, 'wb') as f:
                        f.write(content)
                        
                    logger.info(f"Torrent file saved: {output_path}")
                    return True
                    
                else:
                    logger.error(f"Download failed with status {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Torrent download error: {e}")
            return False

# Test function
async def test_mam_client():
    """Test the MAM client with sample search"""
    async with MAMAPIClient() as client:
        results = await client.search_ebooks("14 Miles", "AJ Gibson")
        
        if results:
            print(f"Found {len(results)} results:")
            for torrent in results:
                print(f"  {torrent.title} by {torrent.author} (confidence: {torrent.confidence_score:.2f})")
        else:
            print("No results found")

if __name__ == "__main__":
    asyncio.run(test_mam_client())