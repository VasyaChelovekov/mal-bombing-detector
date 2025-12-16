"""
MAL Bombing Detector - Main Module

Integrates all system components:
- Data collection from MyAnimeList
- Score distribution analysis
- Review bombing metrics calculation
- Results visualization
- Excel export

This module provides both a CLI entry point and a Python API.
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# Path configuration
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from src.core.analyzer import BombingAnalyzer, AnalysisResult  # noqa: E402
from src.core.metrics import MetricsCalculator  # noqa: E402
from src.core.models import AnimeData, SuspicionLevel  # noqa: E402
from src.platforms import get_platform  # noqa: E402
from src.utils.logging import setup_logging, get_logger  # noqa: E402
from src.utils.config import get_config  # noqa: E402

# Setup logging
logger = get_logger(__name__)


class MALBombingAnalyzer:
    """
    Main class for review bombing analysis on MyAnimeList.

    This class orchestrates the analysis workflow using the new
    modular architecture with async data collection.

    Example:
        >>> analyzer = MALBombingAnalyzer(anime_count=100)
        >>> results = asyncio.run(analyzer.run_full_analysis())
    """

    def __init__(
        self,
        use_cache: bool = True,
        anime_count: int = 50,
        platform_name: str = "myanimelist",
    ):
        """
        Initialize analyzer.

        Args:
            use_cache: Whether to use data cache
            anime_count: Number of anime to analyze
            platform_name: Platform to analyze (myanimelist, anilist, kitsu)
        """
        self.anime_count = anime_count
        self.use_cache = use_cache
        self.platform_name = platform_name

        self.config = get_config()
        self.metrics_calculator = MetricsCalculator()
        self.analyzer = BombingAnalyzer()

        # Results
        self.anime_list: List[AnimeData] = []
        self.results: Optional[AnalysisResult] = None

    async def collect_data(self) -> List[AnimeData]:
        """
        Collect data from the anime platform.

        Returns:
            List of anime data with score distributions.
        """
        logger.info(f"Starting data collection for top-{self.anime_count} anime...")

        platform = get_platform(self.platform_name)

        async with platform:
            # Get top anime list
            top_anime = await platform.get_top_anime(limit=self.anime_count)
            logger.info(f"Fetched {len(top_anime)} anime from rankings")

            # Get detailed stats for each
            self.anime_list = []
            for anime in top_anime:
                try:
                    stats = await platform.get_anime_stats(anime.mal_id)
                    if stats and stats.distribution:
                        stats.rank = anime.rank
                        stats.members = anime.members or stats.members
                        self.anime_list.append(stats)
                except Exception as e:
                    logger.warning(f"Failed to get stats for {anime.mal_id}: {e}")

            logger.info(f"Collected stats for {len(self.anime_list)} anime")

        return self.anime_list

    def analyze(self) -> AnalysisResult:
        """
        Analyze collected data for review bombing patterns.

        Returns:
            AnalysisResult with metrics for each anime.
        """
        if not self.anime_list:
            logger.warning("No data for analysis. Run collect_data() first.")
            return None

        logger.info("Starting bombing analysis...")

        self.results = self.analyzer.analyze_batch(self.anime_list)

        logger.info("Analysis complete. Found:")
        logger.info(f"  - Critical: {self.results.summary.critical_count}")
        logger.info(f"  - High: {self.results.summary.high_count}")
        logger.info(f"  - Medium: {self.results.summary.medium_count}")
        logger.info(f"  - Low: {self.results.summary.low_count}")

        return self.results

    def print_top_bombed(self, n: int = 20):
        """
        Print top-N anime with highest bombing suspicion.

        Args:
            n: Number of results to display
        """
        if not self.results:
            print("No data to display. Run analysis first.")
            return

        print("\n" + "=" * 80)
        print(f"TOP-{n} ANIME WITH HIGHEST REVIEW BOMBING SUSPICION")
        print("=" * 80)

        top_metrics = self.results.get_top(n)

        for m in top_metrics:
            level_emoji = {
                SuspicionLevel.CRITICAL: "🔴",
                SuspicionLevel.HIGH: "🟠",
                SuspicionLevel.MEDIUM: "🟡",
                SuspicionLevel.LOW: "🟢",
            }.get(m.suspicion_level, "⚪")

            print(f"\n#{m.bombing_rank:3d} {level_emoji} {m.title[:50]}")
            print(
                f"     Bombing Score: {m.bombing_score:.2f} ({m.suspicion_level.value.upper()})"
            )
            print(
                f"     Score '1': {m.ones_percentage:.2f}% | "
                f"Score '10': {m.tens_percentage:.2f}%"
            )
            print(
                f"     Z-score: {m.ones_zscore:.3f} | "
                f"Spike: {m.spike_ratio:.3f} | "
                f"Effect: {m.distribution_effect_size:.3f}"
            )

            if m.anomaly_flags:
                flags = ", ".join(m.anomaly_flags[:3])
                print(f"     Flags: {flags}")

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        summary = self.results.summary
        print(f"Total analyzed: {summary.total_analyzed} anime")
        print(f"Mean Bombing Score: {summary.score_mean:.2f}")

        print("\nDistribution by levels:")
        print(f"  🔴 Critical: {summary.critical_count}")
        print(f"  🟠 High: {summary.high_count}")
        print(f"  🟡 Medium: {summary.medium_count}")
        print(f"  🟢 Low: {summary.low_count}")

    async def run_full_analysis(self) -> dict:
        """
        Run complete analysis workflow.

        Returns:
            Dictionary with analysis results and metadata.
        """
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("MAL BOMBING DETECTOR v1.0")
        logger.info("=" * 60)

        try:
            # 1. Data collection
            await self.collect_data()

            # 2. Analysis
            self.analyze()

            # 3. Display results
            self.print_top_bombed()

            elapsed = datetime.now() - start_time
            logger.info(
                f"\nAnalysis completed in {elapsed.total_seconds():.1f} seconds"
            )

            return {
                "anime_count": len(self.anime_list),
                "results": self.results,
                "summary": self.results.summary if self.results else None,
                "elapsed_seconds": elapsed.total_seconds(),
            }

        except Exception as e:
            logger.error(f"Error during analysis: {e}")
            raise


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(
        description="MAL Bombing Detector - vote brigading detection on MyAnimeList"
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=50,
        help="Number of top anime to analyze (default: 50)",
    )
    parser.add_argument(
        "-p",
        "--platform",
        type=str,
        default="myanimelist",
        help="Platform to analyze (default: myanimelist)",
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Do not use cache (reload all data)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(level=log_level)

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         MAL BOMBING DETECTOR v1.0                            ║
    ║         Vote brigading detection on anime platforms          ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    analyzer = MALBombingAnalyzer(
        use_cache=not args.no_cache, anime_count=args.count, platform_name=args.platform
    )

    try:
        results = asyncio.run(analyzer.run_full_analysis())

        print("\n✅ Analysis completed successfully!")
        print(f"   Analyzed: {results['anime_count']} anime")
        print(f"   Execution time: {results['elapsed_seconds']:.1f} sec")

    except KeyboardInterrupt:
        print("\n\n❌ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        logger.exception("Critical error")
        sys.exit(1)


if __name__ == "__main__":
    main()
