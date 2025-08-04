"""
Cache utilities for HealthLang AI MVP
"""

import asyncio
import hashlib
import json
import time
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta

from app.utils.logger import get_logger

logger = get_logger(__name__)


class Cache:
    """Simple in-memory cache with TTL support"""
    
    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
        
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate a cache key from arguments"""
        # Create a string representation of the arguments
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                return None
                
            item = self._cache[key]
            if self._is_expired(item):
                del self._cache[key]
                return None
                
            return item["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set a value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        async with self._lock:
            ttl = ttl or self.default_ttl
            expiry = datetime.now() + timedelta(seconds=ttl)
            
            self._cache[key] = {
                "value": value,
                "expiry": expiry,
                "created": datetime.now()
            }
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from cache
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cached items"""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup(self) -> int:
        """
        Remove expired items from cache
        
        Returns:
            Number of items removed
        """
        async with self._lock:
            expired_keys = [
                key for key, item in self._cache.items()
                if self._is_expired(item)
            ]
            
            for key in expired_keys:
                del self._cache[key]
                
            return len(expired_keys)
    
    def _is_expired(self, item: Dict[str, Any]) -> bool:
        """Check if a cache item is expired"""
        return datetime.now() > item["expiry"]
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            total_items = len(self._cache)
            expired_items = sum(1 for item in self._cache.values() if self._is_expired(item))
            valid_items = total_items - expired_items
            
            return {
                "total_items": total_items,
                "valid_items": valid_items,
                "expired_items": expired_items,
                "default_ttl": self.default_ttl
            }


# Global cache instance
_cache: Optional[Cache] = None


def get_cache() -> Cache:
    """Get the global cache instance"""
    global _cache
    if _cache is None:
        _cache = Cache()
    return _cache


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from the global cache"""
    return await get_cache().get(key)


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Set a value in the global cache"""
    await get_cache().set(key, value, ttl)


async def cache_delete(key: str) -> bool:
    """Delete a key from the global cache"""
    return await get_cache().delete(key)


async def cache_clear() -> None:
    """Clear the global cache"""
    await get_cache().clear() 