"""
Advanced caching system for improved performance
"""

import json
import hashlib
import time
from typing import Any, Optional, Dict, List
from functools import wraps
from pathlib import Path
import asyncio
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(self, value: Any, ttl: Optional[float] = None):
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def access(self) -> Any:
        """Access the cached value and update metadata"""
        self.access_count += 1
        self.last_accessed = time.time()
        return self.value


class MemoryCache:
    """In-memory cache with TTL and LRU eviction"""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[float] = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self._lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                # Sanitize key for logging
                safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
                logger.debug(f"Cache entry expired: {safe_key}")
                return None

            return entry.access()

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in cache"""
        async with self._lock:
            if ttl is None:
                ttl = self.default_ttl

            # Evict if at max size
            if len(self.cache) >= self.max_size and key not in self.cache:
                await self._evict_lru()

            self.cache[key] = CacheEntry(value, ttl)
            # Sanitize key for logging
            safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
            logger.debug(f"Cache entry set: {safe_key}")

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                # Sanitize key for logging
                safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
                logger.debug(f"Cache entry deleted: {safe_key}")
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self.cache.clear()
            logger.debug("Cache cleared")

    async def _evict_lru(self) -> None:
        """Evict least recently used entry"""
        if not self.cache:
            return

        lru_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        del self.cache[lru_key]
        # Sanitize key for logging
        safe_key = ''.join(c for c in lru_key if ord(c) >= 32 or c in ' \t')[:50]
        logger.debug(f"LRU evicted: {safe_key}")

    async def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            total_entries = len(self.cache)
            expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())

            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "active_entries": total_entries - expired_entries,
                "max_size": self.max_size,
                "hit_rate": getattr(self, "_hit_count", 0) / max(getattr(self, "_access_count", 1), 1)
            }


class FileCache:
    """File-based cache for persistent storage"""

    def __init__(self, cache_dir: str = "cache", default_ttl: Optional[float] = None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()

    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key with security validation"""
        # Sanitize key to prevent path traversal
        safe_key = ''.join(c for c in key if c.isalnum() or c in '_-')[:100]
        if not safe_key:
            safe_key = 'default'
        
        # Use SHA-256 instead of MD5 for security (CWE-327 fix)
        key_hash = hashlib.sha256(safe_key.encode()).hexdigest()
        cache_path = self.cache_dir / f"{key_hash}.cache"
        
        # Ensure the resolved path is within cache directory
        if not str(cache_path.resolve()).startswith(str(self.cache_dir.resolve())):
            raise ValueError("Invalid cache path")
        
        return cache_path

    async def get(self, key: str) -> Optional[Any]:
        """Get value from file cache"""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            async with self._lock:
                # Use JSON instead of pickle for security (CWE-502 fix)
                with open(cache_path, 'r', encoding='utf-8') as f:
                    entry_data = json.load(f)

                entry = CacheEntry(
                    entry_data['value'],
                    entry_data.get('ttl')
                )
                entry.created_at = entry_data['created_at']

                if entry.is_expired():
                    cache_path.unlink()
                    # Sanitize key for logging
                    safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
                    logger.debug(f"File cache entry expired: {safe_key}")
                    return None

                return entry.access()

        except Exception as e:
            # Sanitize key and error for logging
            safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
            safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
            logger.error(f"Error reading cache file {safe_key}: {safe_error}")
            return None

    async def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Set value in file cache"""
        cache_path = self._get_cache_path(key)

        if ttl is None:
            ttl = self.default_ttl

        entry_data = {
            'value': value,
            'created_at': time.time(),
            'ttl': ttl
        }

        try:
            async with self._lock:
                # Use JSON instead of pickle for security (CWE-502 fix)
                def default_serializer(obj):
                    """Custom JSON serializer for complex objects"""
                    if hasattr(obj, '__dict__'):
                        return {'__type__': obj.__class__.__name__, '__data__': obj.__dict__}
                    return str(obj)
                
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(entry_data, f, default=default_serializer, indent=2)
                # Sanitize key for logging
                safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
                logger.debug(f"File cache entry set: {safe_key}")

        except Exception as e:
            # Sanitize key and error for logging
            safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
            safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
            logger.error(f"Error writing cache file {safe_key}: {safe_error}")

    async def delete(self, key: str) -> bool:
        """Delete value from file cache"""
        cache_path = self._get_cache_path(key)

        if cache_path.exists():
            try:
                cache_path.unlink()
                # Sanitize key for logging
                safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
                logger.debug(f"File cache entry deleted: {safe_key}")
                return True
            except Exception as e:
                # Sanitize key and error for logging
                safe_key = ''.join(c for c in key if ord(c) >= 32 or c in ' \t')[:50]
                safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
                logger.error(f"Error deleting cache file {safe_key}: {safe_error}")

        return False

    async def clear(self) -> None:
        """Clear all cache files"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            logger.debug("File cache cleared")
        except Exception as e:
            # Sanitize error for logging
            safe_error = ''.join(c for c in str(e) if ord(c) >= 32 or c in ' \t')[:200]
            logger.error(f"Error clearing file cache: {safe_error}")


class MultiLevelCache:
    """Multi-level cache with memory and file storage"""

    def __init__(
        self,
        memory_cache_size: int = 1000,
        memory_ttl: Optional[float] = 1800,  # 30 minutes
        file_ttl: Optional[float] = 86400,   # 24 hours
        cache_dir: str = "cache"
    ):
        self.memory_cache = MemoryCache(memory_cache_size, memory_ttl)
        self.file_cache = FileCache(cache_dir, file_ttl)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        # Try memory cache first
        value = await self.memory_cache.get(key)
        if value is not None:
            return value

        # Try file cache
        value = await self.file_cache.get(key)
        if value is not None:
            # Promote to memory cache
            await self.memory_cache.set(key, value)
            return value

        return None

    async def set(self, key: str, value: Any, memory_ttl: Optional[float] = None,
                  file_ttl: Optional[float] = None) -> None:
        """Set value in multi-level cache"""
        await asyncio.gather(
            self.memory_cache.set(key, value, memory_ttl),
            self.file_cache.set(key, value, file_ttl)
        )

    async def delete(self, key: str) -> bool:
        """Delete value from both cache levels"""
        memory_deleted, file_deleted = await asyncio.gather(
            self.memory_cache.delete(key),
            self.file_cache.delete(key)
        )
        return memory_deleted or file_deleted

    async def clear(self) -> None:
        """Clear all cache levels"""
        await asyncio.gather(
            self.memory_cache.clear(),
            self.file_cache.clear()
        )


# Cache decorators
def cache_result(cache_instance: MultiLevelCache, ttl: Optional[float] = None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_data = {
                'func': func.__name__,
                'args': args,
                'kwargs': kwargs
            }
            # Use SHA-256 instead of MD5 for security (CWE-327 fix)
            cache_key = hashlib.sha256(
                json.dumps(key_data, sort_keys=True, default=str).encode()
            ).hexdigest()

            # Try to get from cache
            result = await cache_instance.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Execute function and cache result
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await cache_instance.set(cache_key, result, memory_ttl=ttl)
            logger.debug(f"Cache miss for {func.__name__}, result cached")
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we need to handle async cache operations
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(async_wrapper(*args, **kwargs))

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Global cache instances
memory_cache = MemoryCache(max_size=2000, default_ttl=1800)
file_cache = FileCache(cache_dir="cache", default_ttl=86400)
multi_cache = MultiLevelCache()

# Specific caches for different data types
analysis_cache = MultiLevelCache(
    memory_cache_size=500,
    memory_ttl=1800,  # 30 minutes
    file_ttl=86400,   # 24 hours
    cache_dir="cache/analysis"
)

insights_cache = MultiLevelCache(
    memory_cache_size=200,
    memory_ttl=3600,  # 1 hour
    file_ttl=604800,  # 1 week
    cache_dir="cache/insights"
)

reports_cache = MultiLevelCache(
    memory_cache_size=100,
    memory_ttl=1800,  # 30 minutes
    file_ttl=259200,  # 3 days
    cache_dir="cache/reports"
)
