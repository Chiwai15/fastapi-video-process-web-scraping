
import os
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Dict, AsyncGenerator, Awaitable

from dependency_injector import containers, providers
from fastapi import Depends

from core.config import Settings, get_settings
from services.cache.redis_cache import RedisCache
from services.video.video_processor import VideoProcessor
from services.scraper.science_news_scraper import ScienceNewsScraper


# Move static methods to module-level functions
def worker_init(config=None):
    """Initialize each worker process with proper settings."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("worker")
    logger.info("Worker process initialized")
    
    # Set process name for better monitoring
    try:
        import setproctitle
        setproctitle.setproctitle("video_worker")
    except ImportError:
        pass


def process_pool_cleanup(pool):
    """Ensure proper cleanup of the process pool."""
    pool.shutdown(wait=True)


def get_media_paths(settings):
    """Get media paths from settings."""
    return settings.get_media_paths()


class Container(containers.DeclarativeContainer):
    """Dependency Injection Container with async support."""
    
    # Configuration
    config = providers.Singleton(get_settings)
    
    # Shared resources
    process_pool = providers.Resource(
        ProcessPoolExecutor,
        max_workers=config.provided.MAX_WORKERS,
        initializer=worker_init,  # Use module-level function
        initargs=(config.provided,)  # Pass config to workers
    )
    
    # Cache service - now uses async Redis
    redis_cache = providers.Singleton(
        RedisCache,
        host=config.provided.REDIS_HOST,
        port=config.provided.REDIS_PORT,
        db=config.provided.REDIS_DB,
        ttl=config.provided.CACHE_TTL
    )

    # Services
    video_processor = providers.Factory(
        VideoProcessor,
        process_pool=process_pool,
        media_paths=providers.Callable(get_media_paths, config),
    )
    
    science_news_scraper = providers.Factory(
        ScienceNewsScraper,
        cache=redis_cache,
        url=config.provided.SCIENCE_NEWS_URL,
        ttl=config.provided.CACHE_TTL
    )


# Create and configure the container
container = Container()

# Async dependency providers for FastAPI
async def get_video_processor() -> VideoProcessor:
    return container.video_processor()

async def get_science_news_scraper() -> ScienceNewsScraper:
    return container.science_news_scraper()

async def get_process_pool() -> ProcessPoolExecutor:
    return container.process_pool()

async def get_redis_cache() -> RedisCache:
    return container.redis_cache()