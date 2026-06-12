from __future__ import annotations

import threading
import time
from typing import Any, Hashable, Optional, Tuple


class _TTLCache:
    """
    Very small in-memory TTL cache.

    This is process-local and primarily intended as a lightweight performance
    boost for read-heavy endpoints. For production, replace with Redis or
    another shared cache backend.
    """

    def __init__(self) -> None:
        self._store: dict[Hashable, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> Optional[Any]:
        now = time.time()
        with self._lock:
            value = self._store.get(key)
            if not value:
                return None
            expires_at, payload = value
            if expires_at < now:
                # expired
                self._store.pop(key, None)
                return None
            return payload

    def set(self, key: Hashable, value: Any, ttl_seconds: int) -> None:
        expires_at = time.time() + ttl_seconds
        with self._lock:
            self._store[key] = (expires_at, value)


_cache = _TTLCache()


def cache_get(key: Hashable) -> Optional[Any]:
    """Fetch a value from the in-memory cache if it has not expired."""
    return _cache.get(key)


def cache_set(key: Hashable, value: Any, ttl_seconds: int) -> None:
    """Store a value in the in-memory cache with a given TTL in seconds."""
    _cache.set(key, value, ttl_seconds)
