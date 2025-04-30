from fastapi import APIRouter, Depends, status
from typing import Dict

from core.dependencies import get_redis_cache
from services.cache.redis_cache import RedisCache

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check(
    cache: RedisCache = Depends(get_redis_cache)
) -> Dict[str, str]:
    """
    Health check endpoint to verify service status.
    
    Checks connectivity to Redis and returns service status.
    
    Returns:
        Dictionary with service status
    """
    # Check Redis connection
    try:
        redis_client = await cache.get_client()
        redis_status = "up" if await redis_client.ping() else "down"
    except Exception:
        redis_status = "down"
    
    return {
        "status": "healthy",
        "redis": redis_status
    }

