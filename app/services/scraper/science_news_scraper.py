import logging
from typing import Dict, List, Optional
import aiohttp
from bs4 import BeautifulSoup

from app.core.decorators import error_handler, timing_decorator
from app.core.exceptions import ScraperError
from app.services.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)

# Define news item structure
NewsItem = Dict[str, str]


class ScienceNewsScraper:
    """Async Scraper for Science News Magazine."""
    
    def __init__(
        self, 
        cache: RedisCache,
        url: str = "https://www.sciencenews.org/",
        ttl: int = 600
    ):
        """
        Initialize scraper.
        
        Args:
            cache: Cache service for storing scraped data
            url: Base URL for Science News Magazine
            ttl: Cache TTL in seconds (default: 10 minutes)
        """
        self.cache = cache
        self.base_url = url
        self.cache_ttl = ttl
        self.cache_key = "trending_science_news"
    
    @error_handler(
        error_map={
            aiohttp.ClientError: ScraperError,
            ValueError: ScraperError
        },
        default_error=ScraperError,
        log_traceback=True
    )
    @timing_decorator(log_level=logging.INFO)  # Using INFO level for better visibility
    async def get_trending_news(self, force_refresh: bool = False) -> List[NewsItem]:
        """
        Get trending news from Science News Magazine asynchronously.
        
        Args:
            force_refresh: Whether to force a refresh of the cache
            
        Returns:
            List of news items with category, title, author, and image URL
        """
        # Check cache first unless forcing refresh
        if not force_refresh:
            cached_data = await self.cache.get(self.cache_key)
            if cached_data:
                logger.info("Returning cached trending news")
                return cached_data
        
        logger.info("Scraping fresh trending news data")
        news_items = await self._scrape_trending_news()
        
        # Cache the results
        await self.cache.set(self.cache_key, news_items, ttl=self.cache_ttl)
        
        return news_items
    
    @timing_decorator(log_level=logging.INFO)  # Also time the scraping function itself
    async def _scrape_trending_news(self) -> List[NewsItem]:
        """
        Scrape trending news from Science News Magazine homepage carousel asynchronously.
        
        Returns:
            List of news items
            
        Raises:
            ScraperError: If scraping fails
        """
        # Create a new session for this request instead of reusing
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch the web page
                logger.debug(f"Fetching page from {self.base_url}")
                async with session.get(self.base_url, timeout=10) as response:
                    response.raise_for_status()
                    html_content = await response.text()
                
                logger.debug("Parsing HTML content")
                # Parse HTML
                soup = BeautifulSoup(html_content, 'lxml')
                
                # Find the carousel section
                carousel = soup.find('ol', class_='carousel__slides___eKqkJ')
                
                # Find carousel articles
                articles = carousel.find_all('li', class_='carousel__wrapper___wIECZ')[:10]
                logger.debug(f"Found {len(articles)} articles in carousel")
                
                return self._parse_carousel_articles(articles)
            
            except Exception as e:
                logger.error(f"Error scraping trending news: {str(e)}")
                raise ScraperError(f"Failed to scrape trending news: {str(e)}")
    
    def _parse_carousel_articles(self, articles) -> List[NewsItem]:
        """
        Parse carousel articles from HTML elements.
        
        Args:
            articles: List of carousel article HTML elements
            
        Returns:
            List of parsed news items
        """
        results = []
        
        for article in articles:
            try:
                # Title
                title_tag = article.find('h3', class_='carousel__title___1uDeB')
                title = title_tag.get_text(strip=True) if title_tag else "Unknown Title"
                
                # Category
                category_tag = article.find('a', class_='carousel__eyebrow___VMI-N')
                category = category_tag.get_text(strip=True) if category_tag else "Science"
                
                # Author(s)
                author_tags = article.find_all('a', class_='byline-link')
                authors = ', '.join(a.get_text(strip=True) for a in author_tags) if author_tags else "Science News Staff"
                
                # Image
                image_tag = article.find('img')
                image_url = image_tag['src'] if image_tag and image_tag.has_attr('src') else ""
                
                # Create news item
                news_item = {
                    "category": category,
                    "title": title,
                    "author": authors,
                    "image_url": image_url
                }
                
                results.append(news_item)
            
            except Exception as e:
                logger.warning(f"Error parsing carousel article: {str(e)}")
                continue
        
        logger.debug(f"Successfully parsed {len(results)} news items")
        return results
    
