"""
Core analyzer for review bombing detection.

This module provides the main analysis engine that orchestrates
the entire bombing detection process.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from ..utils.config import get_config_view
from ..utils.logging import get_logger
from ..utils.i18n import t
from .models import (
    AnalysisSummary,
    AnimeData,
    FailureRecord,
    FailureStage,
    ReviewBombingMetrics,
    SuspicionLevel,
)
from .metrics import MetricsCalculator


logger = get_logger(__name__)


class BombingAnalyzer:
    """
    Main analyzer for review bombing detection.

    Orchestrates the analysis process:
    1. Calculates metrics for each anime
    2. Ranks by bombing score
    3. Generates summary statistics

    Example:
        >>> analyzer = BombingAnalyzer()
        >>> results = analyzer.analyze_batch(anime_list)
        >>> for r in results.metrics:
        ...     print(f"{r.title}: {r.bombing_score}")
    """

    def __init__(self, calculator: Optional[MetricsCalculator] = None):
        """
        Initialize the analyzer.

        Args:
            calculator: Optional custom metrics calculator.
        """
        self.config = get_config_view()
        self.calculator = calculator or MetricsCalculator()

    def analyze_single(self, anime: AnimeData) -> ReviewBombingMetrics:
        """
        Analyze a single anime for review bombing.

        Args:
            anime: Anime data with distribution.

        Returns:
            Bombing metrics for the anime.
        """
        logger.debug(f"Analyzing {anime.title} (ID: {anime.mal_id})")

        try:
            metrics = self.calculator.calculate(anime)
            logger.debug(
                f"  Score: {metrics.bombing_score:.2f}, "
                f"Level: {metrics.suspicion_level}"
            )
            return metrics
        except Exception as e:
            logger.error(f"Error analyzing {anime.mal_id}: {e}")
            raise

    def analyze_batch(
        self,
        anime_list: List[AnimeData],
        progress_callback: Optional[callable] = None,
        total_requested: int = 0,
        fetch_failures: Optional[List[FailureRecord]] = None,
    ) -> AnalysisResult:
        """
        Analyze multiple anime for review bombing.

        Args:
            anime_list: List of anime to analyze.
            progress_callback: Optional callback for progress updates.
                             Called with (current, total).
            total_requested: Total number of anime originally requested.
            fetch_failures: List of failures from the fetch stage.

        Returns:
            AnalysisResult with metrics and summary.
        """
        logger.info(t("analysis.start"))

        metrics_list: List[ReviewBombingMetrics] = []
        failures: List[FailureRecord] = list(fetch_failures) if fetch_failures else []
        skipped_count = 0

        total = len(anime_list)

        for i, anime in enumerate(anime_list):
            try:
                # Skip if no distribution data
                if anime.distribution is None:
                    logger.warning(f"No distribution for {anime.mal_id}, skipping")
                    skipped_count += 1
                    continue

                # Skip if too few votes
                if (
                    anime.distribution.total_votes
                    < self.config.analysis.min_votes_threshold
                ):
                    logger.debug(f"Too few votes for {anime.mal_id}, skipping")
                    skipped_count += 1
                    continue

                metrics = self.analyze_single(anime)
                metrics_list.append(metrics)

            except Exception as e:
                logger.warning(f"Failed to analyze {anime.mal_id}: {e}")
                failures.append(
                    FailureRecord.from_exception(
                        mal_id=anime.mal_id,
                        title=anime.title,
                        url=anime.url,
                        stage=FailureStage.ANALYZE,
                        error=e,
                    )
                )

            if progress_callback:
                progress_callback(i + 1, total)

        # Rank by bombing score
        metrics_list = self.calculator.rank_by_bombing(metrics_list)

        # Generate summary with tracking info
        summary = self._generate_summary(
            metrics_list,
            total_requested=total_requested or total,
            total_failed=len(failures),
            total_skipped=skipped_count,
        )

        # Log results
        logger.info(t("analysis.complete"))
        logger.info(f"  {t('analysis.critical_count', count=summary.critical_count)}")
        logger.info(f"  {t('analysis.high_count', count=summary.high_count)}")

        return AnalysisResult(
            metrics=metrics_list,
            summary=summary,
            failures=failures,
        )

    def _generate_summary(
        self,
        metrics_list: List[ReviewBombingMetrics],
        total_requested: int = 0,
        total_failed: int = 0,
        total_skipped: int = 0,
    ) -> AnalysisSummary:
        """Generate summary statistics from metrics list."""
        if not metrics_list:
            return AnalysisSummary(
                total_analyzed=0,
                total_requested=total_requested,
                total_failed=total_failed,
                total_skipped=total_skipped,
            )

        scores = [m.bombing_score for m in metrics_list]
        ones_pcts = [m.ones_percentage for m in metrics_list]

        # Count by bombing_score thresholds (Fix C - pure score-based)
        # This ensures consistency: level is derived from score ranges
        thresholds = self.config.analysis.suspicion_thresholds
        critical_count = sum(1 for s in scores if s >= thresholds.critical)
        high_count = sum(
            1 for s in scores if thresholds.high <= s < thresholds.critical
        )
        medium_count = sum(
            1 for s in scores if thresholds.medium <= s < thresholds.high
        )
        low_count = sum(1 for s in scores if s < thresholds.medium)

        return AnalysisSummary(
            total_analyzed=len(metrics_list),
            total_requested=total_requested,
            total_failed=total_failed,
            total_skipped=total_skipped,
            score_mean=round(float(np.mean(scores)), 2),
            score_median=round(float(np.median(scores)), 2),
            score_std=round(float(np.std(scores)), 2),
            score_min=round(float(min(scores)), 2),
            score_max=round(float(max(scores)), 2),
            ones_mean=round(float(np.mean(ones_pcts)), 2),
            ones_median=round(float(np.median(ones_pcts)), 2),
            ones_max=round(float(max(ones_pcts)), 2),
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
        )


class AnalysisResult:
    """
    Container for analysis results.

    Attributes:
        metrics: List of bombing metrics for each anime.
        summary: Summary statistics.
        failures: List of FailureRecord for items that failed at any stage.
    """

    def __init__(
        self,
        metrics: List[ReviewBombingMetrics],
        summary: AnalysisSummary,
        failures: Optional[List[FailureRecord]] = None,
    ):
        self.metrics = metrics
        self.summary = summary
        self.failures = failures or []

    @property
    def critical(self) -> List[ReviewBombingMetrics]:
        """Get metrics with critical suspicion level."""
        return [m for m in self.metrics if m.suspicion_level == SuspicionLevel.CRITICAL]

    @property
    def high(self) -> List[ReviewBombingMetrics]:
        """Get metrics with high suspicion level."""
        return [m for m in self.metrics if m.suspicion_level == SuspicionLevel.HIGH]

    @property
    def suspicious(self) -> List[ReviewBombingMetrics]:
        """Get metrics with medium, high, or critical suspicion (score >= 35)."""
        return [
            m
            for m in self.metrics
            if m.suspicion_level
            in (SuspicionLevel.CRITICAL, SuspicionLevel.HIGH, SuspicionLevel.MEDIUM)
        ]

    @property
    def highly_suspicious(self) -> List[ReviewBombingMetrics]:
        """Get metrics with high or critical suspicion (score >= 55)."""
        return [
            m
            for m in self.metrics
            if m.suspicion_level in (SuspicionLevel.CRITICAL, SuspicionLevel.HIGH)
        ]

    @property
    def has_failures(self) -> bool:
        """Check if any failures occurred."""
        return len(self.failures) > 0

    @property
    def failed_ids(self) -> List[int]:
        """Get list of failed anime IDs."""
        return [f.mal_id for f in self.failures]

    def get_top(self, n: int = 10) -> List[ReviewBombingMetrics]:
        """Get top N by bombing score."""
        return self.metrics[:n]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "metrics": [m.to_dict() for m in self.metrics],
            "summary": self.summary.to_dict(),
            "failures": [f.to_dict() for f in self.failures],
        }
