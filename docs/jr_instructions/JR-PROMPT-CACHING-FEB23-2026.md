# Jr Instruction: Prompt Caching Module

**Kanban**: #1762
**Priority**: 6
**Story Points**: 3
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.

---

## Overview

Create a thread-safe LRU prompt caching module for council specialist system prompts. This reduces redundant prompt construction when the same specialist is invoked repeatedly within a short window. Cache is keyed on sha256 of specialist name + prompt version, limited to 50 entries, with 1-hour TTL. This is a library module imported by other components -- no main block needed.

---

## Steps

### Step 1: Create the prompt cache module

Create `/ganuda/lib/prompt_cache.py`

```python
"""
Prompt Cache - Thread-safe LRU cache for council specialist system prompts.
Kanban #1762 - Cherokee AI Federation

Usage:
    from lib.prompt_cache import get_cached_prompt, set_cached_prompt, invalidate_cache

    # Store a prompt
    set_cached_prompt("Coyote", "v2", prompt_text)

    # Retrieve (returns None if expired or missing)
    prompt = get_cached_prompt("Coyote", "v2")

    # Invalidate all versions for a specialist
    invalidate_cache("Coyote")
"""

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Optional


MAX_CACHE_SIZE = 50
TTL_SECONDS = 3600  # 1 hour


class _CacheEntry:
    """Internal cache entry with TTL tracking and specialist name for invalidation."""

    __slots__ = ("value", "specialist_name", "created_at", "ttl_seconds")

    def __init__(self, value: str, specialist_name: str, ttl_seconds: int = TTL_SECONDS):
        self.value = value
        self.specialist_name = specialist_name
        self.created_at = time.monotonic()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        return (time.monotonic() - self.created_at) > self.ttl_seconds


class PromptCache:
    """Thread-safe LRU prompt cache with TTL expiration.

    Keys are sha256(specialist_name + system_prompt_version).
    Max 50 entries. Entries expire after 1 hour.
    Entries store specialist_name for targeted invalidation.
    """

    def __init__(self, max_size: int = MAX_CACHE_SIZE, ttl_seconds: int = TTL_SECONDS):
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
        self._hits = 0
        self._misses = 0

    @staticmethod
    def _make_key(specialist_name: str, version: str) -> str:
        """Generate cache key as sha256 of specialist_name + version."""
        raw = f"{specialist_name}:{version}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, specialist_name: str, version: str) -> Optional[str]:
        """Retrieve a cached prompt. Returns None if missing or expired."""
        key = self._make_key(specialist_name, version)
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                self._misses += 1
                return None
            if entry.is_expired():
                del self._cache[key]
                self._misses += 1
                return None
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry.value

    def set(self, specialist_name: str, version: str, prompt: str) -> None:
        """Store a prompt in the cache. Evicts LRU entry if at capacity."""
        key = self._make_key(specialist_name, version)
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self._max_size:
                # Evict least recently used (first item)
                self._cache.popitem(last=False)
            self._cache[key] = _CacheEntry(
                value=prompt,
                specialist_name=specialist_name,
                ttl_seconds=self._ttl_seconds,
            )

    def invalidate(self, specialist_name: str) -> int:
        """Remove all cached entries for a given specialist (all versions).

        Returns the number of entries removed.
        """
        with self._lock:
            keys_to_remove = [
                k for k, entry in self._cache.items()
                if entry.specialist_name == specialist_name
            ]
            for k in keys_to_remove:
                del self._cache[k]
            return len(keys_to_remove)

    def clear(self) -> None:
        """Clear the entire cache and reset stats."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        """Return cache hit/miss statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_pct": round(hit_rate, 1),
                "ttl_seconds": self._ttl_seconds,
            }


# ---- Module-level singleton and convenience functions ----

_default_cache = PromptCache()


def get_cached_prompt(specialist_name: str, version: str) -> Optional[str]:
    """Get a cached prompt from the default cache instance."""
    return _default_cache.get(specialist_name, version)


def set_cached_prompt(specialist_name: str, version: str, prompt: str) -> None:
    """Store a prompt in the default cache instance."""
    _default_cache.set(specialist_name, version, prompt)


def invalidate_cache(specialist_name: str) -> int:
    """Invalidate all cached prompts for a specialist. Returns count removed."""
    return _default_cache.invalidate(specialist_name)


def clear_cache() -> None:
    """Clear the entire default cache."""
    _default_cache.clear()


def cache_stats() -> dict:
    """Get statistics from the default cache."""
    return _default_cache.stats()
```

---

## Verification

1. Confirm file exists at `/ganuda/lib/prompt_cache.py`
2. Validate syntax: `python3 -c "import ast; ast.parse(open('/ganuda/lib/prompt_cache.py').read())"`
3. Confirm module has NO `if __name__ == "__main__"` block (library only)
4. Confirm thread safety: `threading.Lock` is used in all cache mutation and read operations
5. Confirm cache key is sha256 of specialist_name + version string
6. Confirm MAX_CACHE_SIZE is 50 and TTL_SECONDS is 3600 (1 hour)
7. Confirm module-level convenience functions exist: get_cached_prompt, set_cached_prompt, invalidate_cache, clear_cache, cache_stats
