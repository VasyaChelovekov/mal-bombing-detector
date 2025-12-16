"""
Abstract base class for anime platform adapters.

This module defines the interface that all platform-specific
scrapers must implement, enabling support for multiple
anime databases (MAL, AniList, Kitsu, etc.).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional, AsyncIterator

from ..core.models import AnimeData


class AnimePlatform(ABC):
    """
    Abstract base class for anime platform adapters.

    All platform-specific implementations must inherit from this
    class and implement the required methods.

    This abstraction allows the analyzer to work with any
    anime platform that provides score distribution data.

    Example:
        >>> class MALPlatform(AnimePlatform):
        ...     async def get_top_anime(self, limit: int) -> List[AnimeData]:
        ...         # Implementation
        ...         pass
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the platform name.

        Returns:
            Platform identifier (e.g., "myanimelist", "anilist").
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Get the display name for the platform.

        Returns:
            Human-readable name (e.g., "MyAnimeList", "AniList").
        """
        pass

    @abstractmethod
    async def get_top_anime(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AnimeData]:
        """
        Get top-rated anime from the platform.

        Args:
            limit: Maximum number of anime to retrieve.
            offset: Starting offset for pagination.

        Returns:
            List of AnimeData objects (without full distribution).
        """
        pass

    @abstractmethod
    async def get_anime_stats(
        self,
        anime_id: int,
    ) -> Optional[AnimeData]:
        """
        Get detailed statistics for a specific anime.

        This should include the full score distribution.

        Args:
            anime_id: Platform-specific anime ID.

        Returns:
            AnimeData with full distribution, or None if not found.
        """
        pass

    @abstractmethod
    async def get_anime_by_id(
        self,
        anime_id: int,
    ) -> Optional[AnimeData]:
        """
        Get basic anime information by ID.

        Args:
            anime_id: Platform-specific anime ID.

        Returns:
            AnimeData with basic info, or None if not found.
        """
        pass

    @abstractmethod
    async def search_anime(
        self,
        query: str,
        limit: int = 10,
    ) -> List[AnimeData]:
        """
        Search for anime by title.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching AnimeData objects.
        """
        pass

    async def get_anime_stats_batch(
        self,
        anime_ids: List[int],
        progress_callback: Optional[callable] = None,
    ) -> List[AnimeData]:
        """
        Get statistics for multiple anime.

        Default implementation calls get_anime_stats sequentially.
        Subclasses may override for batch optimization.

        Args:
            anime_ids: List of anime IDs.
            progress_callback: Optional callback(current, total).

        Returns:
            List of AnimeData objects.
        """
        results = []
        total = len(anime_ids)

        for i, anime_id in enumerate(anime_ids):
            try:
                anime = await self.get_anime_stats(anime_id)
                if anime:
                    results.append(anime)
            except Exception:
                pass  # Skip failed entries

            if progress_callback:
                progress_callback(i + 1, total)

        return results

    async def stream_top_anime(
        self,
        limit: int = 50,
        batch_size: int = 25,
    ) -> AsyncIterator[AnimeData]:
        """
        Stream top anime with pagination.

        Yields anime one at a time, fetching in batches.

        Args:
            limit: Total number to retrieve.
            batch_size: Size of each batch.

        Yields:
            AnimeData objects.
        """
        offset = 0
        fetched = 0

        while fetched < limit:
            batch_limit = min(batch_size, limit - fetched)
            anime_list = await self.get_top_anime(batch_limit, offset)

            if not anime_list:
                break

            for anime in anime_list:
                yield anime
                fetched += 1
                if fetched >= limit:
                    break

            offset += len(anime_list)

    async def close(self) -> None:
        """
        Close any open connections.

        Called when the platform is no longer needed.
        Subclasses should override to clean up resources.
        """
        pass

    async def __aenter__(self) -> "AnimePlatform":
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        await self.close()


class PlatformError(Exception):
    """Base exception for platform errors."""

    pass


class RateLimitError(PlatformError):
    """Raised when rate limited by the platform."""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class AuthenticationError(PlatformError):
    """Raised when authentication fails."""

    pass


class NotFoundError(PlatformError):
    """Raised when a resource is not found."""

    pass


class ParseError(PlatformError):
    """Raised when parsing response fails."""

    pass
