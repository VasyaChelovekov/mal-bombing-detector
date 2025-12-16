"""Test stats fetching to diagnose why only 164/1000 succeed."""

import asyncio
import io
import logging
import sys

from src.platforms import get_platform

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
)


async def test():
    plat = get_platform("myanimelist")

    print("\n=== Testing top 100 anime from rankings ===\n")

    async with plat:
        # Get actual top anime from rankings
        top_anime = await plat.get_top_anime(limit=100)
        print(f"Got {len(top_anime)} anime from rankings\n")

        success = 0
        failed = 0

        for anime in top_anime:
            try:
                stats = await plat.get_anime_stats(anime.mal_id)
                if stats and stats.distribution:
                    print(
                        f"[OK] {anime.mal_id}: {stats.title} ({stats.distribution.total_votes:,} votes)"
                    )
                    success += 1
                else:
                    print(
                        f"[FAIL] {anime.mal_id}: {anime.title} - No distribution data"
                    )
                    failed += 1
            except Exception as e:
                print(f"[FAIL] {anime.mal_id}: {anime.title} - Exception: {e}")
                failed += 1

        print(f"\nResults: {success}/{success + failed} succeeded ({failed} failed)")


asyncio.run(test())
