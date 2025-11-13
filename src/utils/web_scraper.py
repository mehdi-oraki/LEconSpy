"""
Web scraping utilities for fetching data from public sources
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import Optional, Dict, Any
from config import USER_AGENT, REQUEST_TIMEOUT, REQUEST_RETRIES

logger = logging.getLogger(__name__)


class WebScraper:
    """Handles web scraping with retry logic and error handling"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def fetch_html(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch HTML content from URL with retry logic
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if failed
        """
        for attempt in range(REQUEST_RETRIES):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < REQUEST_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {REQUEST_RETRIES} attempts")
                    return None
    
    def fetch_json(self, url: str) -> Optional[Dict[Any, Any]]:
        """
        Fetch JSON content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            JSON data as dict or None if failed
        """
        for attempt in range(REQUEST_RETRIES):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < REQUEST_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch JSON from {url}")
                    return None
    
    def fetch_csv(self, url: str) -> Optional[str]:
        """
        Fetch CSV content from URL
        
        Args:
            url: URL to fetch
            
        Returns:
            CSV content as string or None if failed
        """
        for attempt in range(REQUEST_RETRIES):
            try:
                response = self.session.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                return response.text
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < REQUEST_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.error(f"Failed to fetch CSV from {url}")
                    return None

