"""Web scraping functionality for WSWS articles."""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from email.utils import parsedate_to_datetime

import requests
import requests_cache
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WWSSScraper:
    """Scraper for World Socialist Web Site articles."""

    BASE_URL = "https://www.wsws.org"
    RSS_FEED_URL = "https://www.wsws.org/en/rss.xml"

    def __init__(self, timeout: int = 30, cache_enabled: bool = True, cache_expire_minutes: int = 30):
        """Initialize the scraper.

        Args:
            timeout: Request timeout in seconds
            cache_enabled: Whether to enable HTTP caching (default: True)
            cache_expire_minutes: Cache expiration time in minutes (default: 30)
        """
        self.timeout = timeout

        if cache_enabled:
            # Set up cache in a temporary directory
            cache_dir = Path.home() / '.cache' / 'wsws-bulletin'
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Install cache with SQLite backend
            self.session = requests_cache.CachedSession(
                cache_name=str(cache_dir / 'http_cache'),
                backend='sqlite',
                expire_after=cache_expire_minutes * 60,  # Convert to seconds
                allowable_methods=('GET', 'POST'),
                allowable_codes=(200, 304),
                stale_if_error=True,  # Use stale cache if request fails
            )
            logger.debug(f"HTTP cache enabled: {cache_dir / 'http_cache.sqlite'} (expires after {cache_expire_minutes}min)")
        else:
            self.session = requests.Session()
            logger.debug("HTTP cache disabled")

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })

    def get_recent_articles(self, hours: int = 24) -> List[Dict[str, str]]:
        """Get articles published in the last N hours from RSS feed.

        Args:
            hours: Number of hours to look back (default: 24)

        Returns:
            List of dictionaries with article metadata (title, url, date, description)
        """
        logger.info(f"Fetching recent articles from last {hours} hours...")
        response = self.session.get(self.RSS_FEED_URL, timeout=self.timeout)
        response.raise_for_status()

        # Parse RSS XML
        root = ET.fromstring(response.content)
        articles = []
        cutoff_time = datetime.now().astimezone() - timedelta(hours=hours)

        # Find all items in the RSS feed
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            link_elem = item.find('link')
            pubdate_elem = item.find('pubDate')
            description_elem = item.find('description')

            if title_elem is None or link_elem is None or pubdate_elem is None:
                continue

            title = title_elem.text
            url = link_elem.text

            # Parse RFC 822 date format
            try:
                pub_date = parsedate_to_datetime(pubdate_elem.text)

                # Only include articles within the time window
                if pub_date >= cutoff_time:
                    articles.append({
                        'title': title,
                        'url': url,
                        'date': pub_date.strftime('%Y-%m-%d'),
                        'description': description_elem.text if description_elem is not None else ''
                    })
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse date for article: {title} - {e}")
                continue

        logger.info(f"Found {len(articles)} articles from last {hours} hours")
        return articles

    def get_latest_perspective(self) -> Optional[Dict[str, str]]:
        """Get the most recent perspective article from RSS feed.

        Returns:
            Dictionary with perspective metadata (title, url, date) or None
        """
        logger.info("Fetching latest perspective article...")
        response = self.session.get(self.RSS_FEED_URL, timeout=self.timeout)
        response.raise_for_status()

        # Parse RSS XML
        root = ET.fromstring(response.content)

        # Look for perspective articles (URLs containing "pers-")
        for item in root.findall('.//item'):
            title_elem = item.find('title')
            link_elem = item.find('link')
            pubdate_elem = item.find('pubDate')
            description_elem = item.find('description')

            if title_elem is None or link_elem is None:
                continue

            url = link_elem.text

            # Check if this is a perspective article (contains "pers-" in URL)
            if '/pers-' in url:
                title = title_elem.text

                # Parse date
                date_str = None
                if pubdate_elem is not None:
                    try:
                        pub_date = parsedate_to_datetime(pubdate_elem.text)
                        date_str = pub_date.strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        pass

                logger.info(f"Found perspective: {title}")
                return {
                    'title': title,
                    'url': url,
                    'date': date_str,
                    'description': description_elem.text if description_elem is not None else ''
                }

        logger.warning("No perspective article found")
        return None

    def get_article_content(self, url: str) -> Dict[str, str]:
        """Fetch and extract the full content of an article.

        Args:
            url: Article URL

        Returns:
            Dictionary with article content (title, text, date, author)
        """
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Extract title
        title_elem = soup.find('h1')
        title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"

        # Extract article text
        article_body = soup.find('div', class_='article-content') or soup.find('article')

        if article_body:
            # Remove script and style elements
            for script in article_body(['script', 'style']):
                script.decompose()

            # Get text
            paragraphs = article_body.find_all('p')
            text = '\n\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
        else:
            text = ""

        # Extract author
        author_elem = soup.find('span', class_='author') or soup.find('a', rel='author')
        author = author_elem.get_text(strip=True) if author_elem else "Unknown"

        # Extract date
        date_elem = soup.find('time') or soup.find('span', class_='date')
        date = date_elem.get_text(strip=True) if date_elem else "Unknown"

        return {
            'title': title,
            'text': text,
            'author': author,
            'date': date,
            'url': url
        }

    def fetch_all_content(self, hours: int = 24) -> Dict[str, any]:
        """Fetch all articles and perspective with full content.

        Args:
            hours: Number of hours to look back for recent articles

        Returns:
            Dictionary with 'articles' and 'perspective' keys containing full content
        """
        result = {
            'articles': [],
            'perspective': None
        }

        # Get recent articles
        recent_articles = self.get_recent_articles(hours)
        logger.info(f"Fetching content for {len(recent_articles)} recent articles...")

        for i, article_meta in enumerate(recent_articles, 1):
            logger.debug(f"[{i}/{len(recent_articles)}] {article_meta['title'][:60]}...")
            content = self.get_article_content(article_meta['url'])
            result['articles'].append(content)

        # Get perspective
        perspective_meta = self.get_latest_perspective()
        if perspective_meta:
            logger.info("Fetching perspective content...")
            result['perspective'] = self.get_article_content(perspective_meta['url'])

        return result
