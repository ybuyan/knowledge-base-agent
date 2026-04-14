import hashlib
import logging
from collections import OrderedDict
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingCache:
    def __init__(self, maxsize: int = 1000):
        self._cache: OrderedDict = OrderedDict()
        self._maxsize = maxsize
        self._hits = 0
        self._misses = 0

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> Optional[List[float]]:
        key = self._hash(text)
        if key in self._cache:
            self._cache.move_to_end(key)
            self._hits += 1
            logger.debug(f"Embedding缓存命中: {key[:8]}...")
            return self._cache[key]
        self._misses += 1
        return None

    def set(self, text: str, embedding: List[float]):
        key = self._hash(text)
        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = embedding
        if len(self._cache) > self._maxsize:
            evicted = self._cache.popitem(last=False)
            logger.debug(f"Embedding缓存淘汰: {evicted[0][:8]}...")

    def stats(self) -> dict:
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2%}",
        }


embedding_cache = EmbeddingCache(maxsize=1000)
