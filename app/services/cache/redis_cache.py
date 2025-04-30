import json
import logging
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as aioredis

from core.decorators import error_handler
from core.exceptions import CacheError

logger = logging.getLogger(__name__)


class RedisCache:
    """Async Redis-based cache implementation."""
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        db: int = 0, 
        ttl: int = 600
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            ttl: Default time-to-live (seconds)
        """
        self.host = host
        self.port = port
        self.db = db
        self.default_ttl = ttl
        self._client = None
        self._url = f"redis://{host}:{port}/{db}"
    
    async def _connect(self) -> None:
        """Establish connection to Redis asynchronously."""
        try:
            self._client = await aioredis.from_url(
                self._url,
                decode_responses=True
            )
            # Test the connection
            await self._client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Redis connection error: {str(e)}")
            raise CacheError(f"Failed to connect to Redis: {str(e)}")
    
    async def get_client(self) -> aioredis.Redis:
        """Get Redis client, reconnecting if needed."""
        if self._client is None:
            await self._connect()
        return self._client
    
    @error_handler(
        error_map={Exception: CacheError},
        default_error=CacheError,
        log_traceback=True
    )
    async def get(self, key: str) -> Any:
        """
        Get value from cache asynchronously.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
            
        Raises:
            CacheError: If Redis operation fails
        """
        client = await self.get_client()
        data = await client.get(key)
        if data is None:
            return None
        
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            # Not JSON data, return as is
            return data
    
    @error_handler(
        error_map={Exception: CacheError},
        default_error=CacheError,
        log_traceback=True
    )
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache asynchronously.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if successful
            
        Raises:
            CacheError: If Redis operation fails
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # Serialize value
        try:
            if isinstance(value, (dict, list, tuple, bool, int, float)):
                data = json.dumps(value)
            else:
                data = str(value)
        except Exception as e:
            raise CacheError(f"Failed to serialize value: {str(e)}")
        
        client = await self.get_client()
        return await client.setex(key, ttl, data)
    
    @error_handler(
        error_map={Exception: CacheError},
        default_error=CacheError,
        log_traceback=True
    )
    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache asynchronously.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if key didn't exist
            
        Raises:
            CacheError: If Redis operation fails
        """
        client = await self.get_client()
        return bool(await client.delete(key))
    
    @error_handler(
        error_map={Exception: CacheError},
        default_error=CacheError,
        log_traceback=True
    )
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache asynchronously.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
            
        Raises:
            CacheError: If Redis operation fails
        """
        client = await self.get_client()
        return bool(await client.exists(key))
    
    @error_handler(
        error_map={Exception: CacheError},
        default_error=CacheError,
        log_traceback=True
    )
    async def clear(self) -> bool:
        """
        Clear all keys in the current database asynchronously.
        
        Returns:
            True if successful
            
        Raises:
            CacheError: If Redis operation fails
        """
        client = await self.get_client()
        return await client.flushdb()
    
    async def close(self) -> None:
        """Close Redis connection asynchronously."""
        if self._client:
            await self._client.close()
            self._client = None