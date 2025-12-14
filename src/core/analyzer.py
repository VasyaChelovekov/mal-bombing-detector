"""
Core analyzer for review bombing detection.

This module provides the main analysis engine that orchestrates
the entire bombing detection process.
"""

from __future__ import annotations

from typing import List, Optional

import numpy as np

from ..utils.config import get_config
from ..utils.logging import get_logger
from ..utils.i18n import t
from .models import (
    AnalysisSummary,
    AnimeData,
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
        self.config = get_config()
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
    ) -> AnalysisResult:
        """
        Analyze multiple anime for review bombing.
        
        Args:
            anime_list: List of anime to analyze.
            progress_callback: Optional callback for progress updates.
                             Called with (current, total).
        
        Returns:
            AnalysisResult with metrics and summary.
        """
        logger.info(t("analysis.start"))
        
        metrics_list: List[ReviewBombingMetrics] = []
        errors: List[tuple] = []
        
        total = len(anime_list)
        
        for i, anime in enumerate(anime_list):
            try:
                # Skip if no distribution data
                if anime.distribution is None:
                    logger.warning(f"No distribution for {anime.mal_id}, skipping")
                    continue
                
                # Skip if too few votes
                if anime.distribution.total_votes < self.config.analysis.min_votes_threshold:
                    logger.debug(f"Too few votes for {anime.mal_id}, skipping")
                    continue
                
                metrics = self.analyze_single(anime)
                metrics_list.append(metrics)
                
            except Exception as e:
                logger.warning(f"Failed to analyze {anime.mal_id}: {e}")
                errors.append((anime.mal_id, str(e)))
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        # Rank by bombing score
        metrics_list = self.calculator.rank_by_bombing(metrics_list)
        
        # Generate summary
        summary = self._generate_summary(metrics_list)
        
        # Log results
        logger.info(t("analysis.complete"))
        logger.info(f"  {t('analysis.critical_count', count=summary.critical_count)}")
        logger.info(f"  {t('analysis.high_count', count=summary.high_count)}")
        
        return AnalysisResult(
            metrics=metrics_list,
            summary=summary,
            errors=errors,
        )
    
    def _generate_summary(
        self,
        metrics_list: List[ReviewBombingMetrics],
    ) -> AnalysisSummary:
        """Generate summary statistics from metrics list."""
        if not metrics_list:
            return AnalysisSummary(
                total_analyzed=0,
                score_mean=0, score_median=0, score_std=0,
                score_min=0, score_max=0,
                ones_mean=0, ones_median=0, ones_max=0,
                critical_count=0, high_count=0,
                medium_count=0, low_count=0,
            )
        
        scores = [m.bombing_score for m in metrics_list]
        ones_pcts = [m.ones_percentage for m in metrics_list]
        
        # Count by level
        level_counts = {
            SuspicionLevel.CRITICAL: 0,
            SuspicionLevel.HIGH: 0,
            SuspicionLevel.MEDIUM: 0,
            SuspicionLevel.LOW: 0,
        }
        for m in metrics_list:
            level_counts[m.suspicion_level] += 1
        
        return AnalysisSummary(
            total_analyzed=len(metrics_list),
            score_mean=round(float(np.mean(scores)), 2),
            score_median=round(float(np.median(scores)), 2),
            score_std=round(float(np.std(scores)), 2),
            score_min=round(float(min(scores)), 2),
            score_max=round(float(max(scores)), 2),
            ones_mean=round(float(np.mean(ones_pcts)), 2),
            ones_median=round(float(np.median(ones_pcts)), 2),
            ones_max=round(float(max(ones_pcts)), 2),
            critical_count=level_counts[SuspicionLevel.CRITICAL],
            high_count=level_counts[SuspicionLevel.HIGH],
            medium_count=level_counts[SuspicionLevel.MEDIUM],
            low_count=level_counts[SuspicionLevel.LOW],
        )


class AnalysisResult:
    """
    Container for analysis results.
    
    Attributes:
        metrics: List of bombing metrics for each anime.
        summary: Summary statistics.
        errors: List of (anime_id, error_message) for failed analyses.
    """
    
    def __init__(
        self,
        metrics: List[ReviewBombingMetrics],
        summary: AnalysisSummary,
        errors: Optional[List[tuple]] = None,
    ):
        self.metrics = metrics
        self.summary = summary
        self.errors = errors or []
    
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
        """Get metrics with high or critical suspicion."""
        return [
            m for m in self.metrics
            if m.suspicion_level in (SuspicionLevel.CRITICAL, SuspicionLevel.HIGH)
        ]
    
    def get_top(self, n: int = 10) -> List[ReviewBombingMetrics]:
        """Get top N by bombing score."""
        return self.metrics[:n]
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'metrics': [m.to_dict() for m in self.metrics],
            'summary': self.summary.to_dict(),
            'errors': self.errors,
        }
