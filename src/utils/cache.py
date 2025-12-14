"""
Cache management for MAL Bombing Detector.

Provides caching functionality with:
- JSON-based file storage
- TTL (Time-To-Live) expiration
- LRU eviction policy
- Optional compression
"""

from __future__ import annotations

import gzip
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Generic, Optional, TypeVar

from .config import get_config, ROOT_DIR


T = TypeVar('T')


class CacheEntry(Generic[T]):
    """
    A single cache entry with metadata.
    
    Attributes:
        data: The cached data.
        created_at: When the entry was created.
        accessed_at: When the entry was last accessed.
        access_count: Number of times accessed.
    """
    
    def __init__(self, data: T, created_at: Optional[datetime] = None):
        self.data = data
        self.created_at = created_at or datetime.now()
        self.accessed_at = self.created_at
        self.access_count = 0
    
    def access(self) -> T:
        """Record access and return data."""
        self.accessed_at = datetime.now()
        self.access_count += 1
        return self.data
    
    def is_expired(self, ttl_hours: int) -> bool:
        """Check if entry is expired based on TTL."""
        expiry = self.created_at + timedelta(hours=ttl_hours)
        return datetime.now() > expiry
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'data': self.data,
            'created_at': self.created_at.isoformat(),
            'accessed_at': self.accessed_at.isoformat(),
            'access_count': self.access_count,
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        entry = cls(
            data=d['data'],
            created_at=datetime.fromisoformat(d['created_at']),
        )
        entry.accessed_at = datetime.fromisoformat(d['accessed_at'])
        entry.access_count = d.get('access_count', 0)
        return entry


class FileCache:
    """
    File-based cache with JSON storage.
    
    Features:
    - Persistent storage to disk
    - TTL-based expiration
    - LRU eviction when max entries exceeded
    - Optional gzip compression
    
    Example:
        >>> cache = FileCache("anime_cache")
        >>> cache.set("12345", {"title": "Naruto", "score": 8.5})
        >>> data = cache.get("12345")
    """
    
    def __init__(
        self,
        name: str,
        cache_dir: Optional[Path] = None,
        ttl_hours: Optional[int] = None,
        max_entries: Optional[int] = None,
        compression: Optional[bool] = None,
    ):
        """
        Initialize file cache.
        
        Args:
            name: Cache name (used for filename).
            cache_dir: Directory for cache files.
            ttl_hours: Time-to-live in hours.
            max_entries: Maximum number of entries.
            compression: Whether to use gzip compression.
        """
        config = get_config()
        
        self.name = name
        self.cache_dir = cache_dir or config.cache.path
        self.ttl_hours = ttl_hours or config.cache.expiry_hours
        self.max_entries = max_entries or config.cache.max_entries
        self.compression = compression if compression is not None else config.cache.compression
        
        self._entries: Dict[str, CacheEntry] = {}
        self._dirty = False
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing cache
        self._load()
    
    @property
    def _cache_file(self) -> Path:
        """Get cache file path."""
        ext = ".json.gz" if self.compression else ".json"
        return self.cache_dir / f"{self.name}{ext}"
    
    def _load(self) -> None:
        """Load cache from disk."""
        if not self._cache_file.exists():
            return
        
        try:
            if self.compression:
                with gzip.open(self._cache_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                with open(self._cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            for key, entry_data in data.get('entries', {}).items():
                self._entries[key] = CacheEntry.from_dict(entry_data)
            
        except (json.JSONDecodeError, OSError, KeyError):
            self._entries = {}
    
    def _save(self) -> None:
        """Save cache to disk."""
        if not self._dirty:
            return
        
        data = {
            'name': self.name,
            'updated_at': datetime.now().isoformat(),
            'entries': {k: v.to_dict() for k, v in self._entries.items()},
        }
        
        try:
            if self.compression:
                with gzip.open(self._cache_file, 'wt', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False)
            else:
                with open(self._cache_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            
            self._dirty = False
            
        except OSError:
            pass
    
    def _evict_lru(self) -> None:
        """Evict least recently used entries if over limit."""
        while len(self._entries) > self.max_entries:
            # Find LRU entry
            lru_key = min(
                self._entries.keys(),
                key=lambda k: self._entries[k].accessed_at
            )
            del self._entries[lru_key]
            self._dirty = True
    
    def _cleanup_expired(self) -> None:
        """Remove expired entries."""
        expired = [
            key for key, entry in self._entries.items()
            if entry.is_expired(self.ttl_hours)
        ]
        for key in expired:
            del self._entries[key]
        if expired:
            self._dirty = True
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key.
        
        Returns:
            Cached value or None if not found/expired.
        """
        entry = self._entries.get(key)
        
        if entry is None:
            return None
        
        if entry.is_expired(self.ttl_hours):
            del self._entries[key]
            self._dirty = True
            return None
        
        return entry.access()
    
    def set(self, key: str, value: Any) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key.
            value: Value to cache.
        """
        self._entries[key] = CacheEntry(value)
        self._dirty = True
        
        # Evict if necessary
        if len(self._entries) > self.max_entries:
            self._evict_lru()
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key.
        
        Returns:
            True if entry existed and was deleted.
        """
        if key in self._entries:
            del self._entries[key]
            self._dirty = True
            return True
        return False
    
    def has(self, key: str) -> bool:
        """
        Check if key exists and is not expired.
        
        Args:
            key: Cache key.
        
        Returns:
            True if key exists and is valid.
        """
        entry = self._entries.get(key)
        if entry is None:
            return False
        if entry.is_expired(self.ttl_hours):
            del self._entries[key]
            self._dirty = True
            return False
        return True
    
    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._dirty = True
    
    def flush(self) -> None:
        """Flush cache to disk."""
        self._cleanup_expired()
        self._save()
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats.
        """
        self._cleanup_expired()
        
        total_accesses = sum(e.access_count for e in self._entries.values())
        
        return {
            'name': self.name,
            'entries': len(self._entries),
            'max_entries': self.max_entries,
            'ttl_hours': self.ttl_hours,
            'total_accesses': total_accesses,
            'compression': self.compression,
            'file_size_bytes': self._cache_file.stat().st_size if self._cache_file.exists() else 0,
        }
    
    def __len__(self) -> int:
        """Get number of entries."""
        return len(self._entries)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return self.has(key)
    
    def __enter__(self) -> 'FileCache':
        """Context manager entry."""
        return self
    
    def __exit__(self, *args) -> None:
        """Context manager exit - flush to disk."""
        self.flush()


# Global cache instances
_caches: Dict[str, FileCache] = {}


def get_cache(name: str = "default") -> FileCache:
    """
    Get or create a named cache instance.
    
    Args:
        name: Cache name.
    
    Returns:
        FileCache instance.
    """
    if name not in _caches:
        _caches[name] = FileCache(name)
    return _caches[name]


def clear_all_caches() -> None:
    """Clear all cache instances."""
    for cache in _caches.values():
        cache.clear()
        cache.flush()
