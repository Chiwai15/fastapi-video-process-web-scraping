from fastapi import APIRouter, Depends, Query
from typing import Dict, List

from app.core.dependencies import get_science_news_scraper
from app.services.scraper.science_news_scraper import ScienceNewsScraper
from app.core.decorators import api_error_handler

router = APIRouter(tags=["Trending News"])


@router.get("/trending-news")
@api_error_handler()
async def get_trending_news(
    refresh: bool = Query(False, description="Force refresh of cached data"),
    scraper: ScienceNewsScraper = Depends(get_science_news_scraper)
) -> List[Dict[str, str]]:
    """
    Get trending news from Science News Magazine asynchronously.
    
    Returns the last 10 trending science news items.
    
    Args:
        refresh: If True, forces a refresh of the cached data
        
    Returns:
        List of news items containing category, title, author, and image URL
    """
    return await scraper.get_trending_news(force_refresh=refresh)