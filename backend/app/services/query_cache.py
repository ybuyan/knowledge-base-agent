"""
Query Cache Service
Provides caching for query optimization results
"""

import hashlib
import time
from typing import Optional, Dict, Any
from collections import OrderedDict
import threading
import logging

logger = logging.getLogger(__name__)


class QueryCache:
    """
    Thread-safe LRU cache for query optimization results.
    Can be easily replaced with Redis for distributed systems.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, max_size: int = 1000, ttl_seconds: int = 86400):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
                    cls._instance._max_size = max_size
                    cls._instance._ttl = ttl_seconds
                    cls._instance._cache_lock = threading.Lock()
                    cls._instance._hits = 0
                    cls._instance._misses = 0
        return cls._instance
    
    def _generate_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.encode('utf-8')).hexdigest()
    
    def _is_expired(self, cached_item: Dict[str, Any]) -> bool:
        """Check if cached item is expired"""
        return time.time() - cached_item['timestamp'] > self._ttl
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached optimization result.
        Returns None if not found or expired.
        """
        key = self._generate_key(query)
        
        with self._cache_lock:
            if key not in self._cache:
                self._misses += 1
                logger.debug(f"Cache miss for query: {query[:50]}...")
                return None
            
            cached_item = self._cache[key]
            
            if self._is_expired(cached_item):
                del self._cache[key]
                self._misses += 1
                logger.debug(f"Cache expired for query: {query[:50]}...")
                return None
            
            self._cache.move_to_end(key)
            self._hits += 1
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return cached_item['data']
    
    def set(self, query: str, result: Dict[str, Any]) -> None:
        """
        Cache optimization result.
        Uses LRU eviction when cache is full.
        """
        key = self._generate_key(query)
        
        with self._cache_lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = {
                    'data': result,
                    'timestamp': time.time()
                }
                return
            
            if len(self._cache) >= self._max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                logger.debug(f"Cache evicted oldest entry")
            
            self._cache[key] = {
                'data': result,
                'timestamp': time.time()
            }
            logger.debug(f"Cached result for query: {query[:50]}...")
    
    def clear(self) -> None:
        """Clear all cached items"""
        with self._cache_lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._cache_lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'size': len(self._cache),
                'max_size': self._max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate': f"{hit_rate:.2f}%",
                'ttl_seconds': self._ttl
            }


query_cache = QueryCache()
