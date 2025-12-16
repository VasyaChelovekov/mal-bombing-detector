"""
Core modules for MAL Bombing Detector.

This package contains the main analysis engine:
- models: Data structures
- statistics: Statistical utilities
- metrics: Bombing metrics calculation
- analyzer: Main analysis orchestrator
"""

from .models import (
    AnimeData,
    AnalysisSummary,
    BombingSeverity,
    ContentType,
    ContextualFactors,
    FailureRecord,
    FailureStage,
    ReviewBombingMetrics,
    ScoreDistribution,
    SeverityLevel,
    SuspicionLevel,
)
from .statistics import (
    DistributionStatistics,
    EffectSizeCalculator,
    ZScoreCalculator,
    get_expected_distribution,
)
from .metrics import MetricsCalculator
from .analyzer import AnalysisResult, BombingAnalyzer

__all__ = [
    # Models
    "AnimeData",
    "AnalysisSummary",
    "BombingSeverity",
    "ContentType",
    "ContextualFactors",
    "FailureRecord",
    "FailureStage",
    "ReviewBombingMetrics",
    "ScoreDistribution",
    "SeverityLevel",
    "SuspicionLevel",
    # Statistics
    "DistributionStatistics",
    "EffectSizeCalculator",
    "ZScoreCalculator",
    "get_expected_distribution",
    # Metrics
    "MetricsCalculator",
    # Analyzer
    "AnalysisResult",
    "BombingAnalyzer",
]
