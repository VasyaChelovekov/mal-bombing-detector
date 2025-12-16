"""
Platform adapters for anime databases.

This package provides platform-specific implementations
for scraping anime data from various sources.

Supported platforms:
- MyAnimeList (myanimelist.py)
- AniList (anilist.py) - planned
- Kitsu (kitsu.py) - planned
"""

from .base import (
    AnimePlatform,
    AuthenticationError,
    NotFoundError,
    ParseError,
    PlatformError,
    RateLimitError,
)
from .myanimelist import MyAnimeListPlatform


# Platform registry
PLATFORMS = {
    "myanimelist": MyAnimeListPlatform,
    "mal": MyAnimeListPlatform,
}


def get_platform(name: str = "myanimelist") -> AnimePlatform:
    """
    Get a platform adapter by name.

    Args:
        name: Platform name (myanimelist, mal, anilist, kitsu).

    Returns:
        Platform adapter instance.

    Raises:
        ValueError: If platform is not supported.

    Example:
        >>> platform = get_platform("myanimelist")
        >>> async with platform as p:
        ...     anime = await p.get_top_anime(10)
    """
    platform_class = PLATFORMS.get(name.lower())

    if platform_class is None:
        available = ", ".join(PLATFORMS.keys())
        raise ValueError(
            f"Platform '{name}' is not supported. Available platforms: {available}"
        )

    return platform_class()


__all__ = [
    # Base
    "AnimePlatform",
    "AuthenticationError",
    "NotFoundError",
    "ParseError",
    "PlatformError",
    "RateLimitError",
    # Implementations
    "MyAnimeListPlatform",
    # Registry
    "PLATFORMS",
    "get_platform",
]
