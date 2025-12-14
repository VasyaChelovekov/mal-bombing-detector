"""
MAL Bombing Detector

A sophisticated tool for detecting and analyzing review bombing patterns
on anime rating platforms like MyAnimeList.

Features:
- Multi-factor statistical detection algorithm
- Comprehensive visualization and reporting
- Multiple export formats (Excel, JSON, CSV, HTML)
- Platform-agnostic design
- Internationalization support
"""

__version__ = "2.0.0"
__author__ = "VasyaChelovekov"
__license__ = "MIT"

from src.core.analyzer import BombingAnalyzer, AnalysisResult
from src.core.metrics import MetricsCalculator
from src.core.models import (
    AnimeData,
    ReviewBombingMetrics,
    BombingSeverity,
    ScoreDistribution,
    SuspicionLevel,
)
from src.platforms import get_platform

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Main classes
    "BombingAnalyzer",
    "MetricsCalculator",
    # Models
    "AnimeData",
    "AnalysisResult",
    "ReviewBombingMetrics",
    "BombingSeverity",
    "ScoreDistribution",
    "SuspicionLevel",
    # Utilities
    "get_platform",
]
