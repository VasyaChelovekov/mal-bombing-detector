"""
Core data models for MAL Bombing Detector.

This module defines the data structures used throughout the application:
- AnimeData: Basic anime information
- ScoreDistribution: Rating distribution data
- ReviewBombingMetrics: Bombing analysis results
- BombingSeverity: Severity classification
- ContextualFactors: Contextual analysis factors
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class SuspicionLevel(str, Enum):
    """Suspicion level classification."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        return self.value


class SeverityLevel(str, Enum):
    """Severity level for bombing impact."""

    EXTREME = "extreme"
    SEVERE = "severe"
    MODERATE = "moderate"
    LIGHT = "light"
    NONE = "none"

    def __str__(self) -> str:
        return self.value


class ContentType(str, Enum):
    """Anime content type."""

    TV = "tv"
    MOVIE = "movie"
    OVA = "ova"
    SPECIAL = "special"
    ONA = "ona"
    MUSIC = "music"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


class FailureStage(str, Enum):
    """Stage at which a failure occurred."""

    FETCH = "fetch"
    PARSE = "parse"
    ANALYZE = "analyze"
    EXPORT = "export"

    def __str__(self) -> str:
        return self.value


@dataclass
class FailureRecord:
    """
    Record of a failed analysis attempt.

    Attributes:
        mal_id: The anime ID that failed.
        url: URL that was being accessed (if applicable).
        title: Anime title if known.
        stage: Stage at which failure occurred.
        error_type: Type/class of the error.
        message: Error message.
        timestamp: When the failure occurred.
    """

    mal_id: int
    stage: FailureStage
    error_type: str
    message: str
    url: str = ""
    title: str = ""
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mal_id": self.mal_id,
            "url": self.url,
            "title": self.title,
            "stage": str(self.stage),
            "error_type": self.error_type,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_exception(
        cls,
        mal_id: int,
        stage: FailureStage,
        error: Exception,
        title: str = "",
        url: str = "",
    ) -> "FailureRecord":
        """Create a failure record from an exception while keeping schema stable."""
        return cls(
            mal_id=mal_id,
            title=title,
            url=url,
            stage=stage,
            error_type=type(error).__name__,
            message=str(error),
        )

    @classmethod
    def from_message(
        cls,
        mal_id: int,
        stage: FailureStage,
        error_type: str,
        message: str,
        title: str = "",
        url: str = "",
    ) -> "FailureRecord":
        """Create a failure record from an explicit error message."""
        return cls(
            mal_id=mal_id,
            title=title,
            url=url,
            stage=stage,
            error_type=error_type,
            message=message,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailureRecord":
        """Create from dictionary."""
        stage = FailureStage.FETCH
        if s := data.get("stage"):
            try:
                stage = FailureStage(s)
            except ValueError:
                pass

        timestamp = None
        if ts := data.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(ts)
            except ValueError:
                pass

        return cls(
            mal_id=data.get("mal_id", 0),
            url=data.get("url", ""),
            title=data.get("title", ""),
            stage=stage,
            error_type=data.get("error_type", "Unknown"),
            message=data.get("message", ""),
            timestamp=timestamp,
        )


@dataclass
class ScoreDistribution:
    """
    Score distribution data for an anime.

    Attributes:
        percentages: Percentage of votes for each score (1-10).
        vote_counts: Absolute vote counts for each score (1-10).
        total_votes: Total number of votes.
    """

    percentages: Dict[int, float] = field(default_factory=dict)
    vote_counts: Dict[int, int] = field(default_factory=dict)
    total_votes: int = 0

    def __post_init__(self):
        """Ensure keys are integers."""
        self.percentages = {int(k): v for k, v in self.percentages.items()}
        self.vote_counts = {int(k): v for k, v in self.vote_counts.items()}

    @property
    def ones_percentage(self) -> float:
        """Get percentage of score 1 votes."""
        return self.percentages.get(1, 0.0)

    @property
    def tens_percentage(self) -> float:
        """Get percentage of score 10 votes."""
        return self.percentages.get(10, 0.0)

    def get_percentage(self, score: int) -> float:
        """Get percentage for a specific score."""
        return self.percentages.get(score, 0.0)

    def get_vote_count(self, score: int) -> int:
        """Get vote count for a specific score."""
        return self.vote_counts.get(score, 0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "percentages": self.percentages,
            "vote_counts": self.vote_counts,
            "total_votes": self.total_votes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScoreDistribution":
        """Create from dictionary."""
        return cls(
            percentages={int(k): v for k, v in data.get("percentages", {}).items()},
            vote_counts={int(k): v for k, v in data.get("vote_counts", {}).items()},
            total_votes=data.get("total_votes", 0),
        )


@dataclass
class AnimeData:
    """
    Basic anime information.

    Attributes:
        mal_id: MyAnimeList ID (or platform-specific ID).
        title: Anime title.
        url: URL to anime page.
        rank: Ranking position.
        score: Average score (1-10).
        members: Number of members/followers.
        distribution: Score distribution data.
        content_type: Type of content (TV, Movie, etc.).
        is_sequel: Whether this is a sequel.
        start_year: Year anime started airing.
        scraped_at: When data was scraped.
    """

    mal_id: int
    title: str
    url: str = ""
    rank: int = 0
    score: float = 0.0
    members: int = 0
    distribution: Optional[ScoreDistribution] = None
    content_type: ContentType = ContentType.UNKNOWN
    is_sequel: bool = False
    start_year: int = 0
    scraped_at: Optional[datetime] = None

    @property
    def total_votes(self) -> int:
        """Get total votes from distribution."""
        if self.distribution:
            return self.distribution.total_votes
        return 0

    @property
    def score_distribution(self) -> Dict[int, float]:
        """Get score percentages (compatibility property)."""
        if self.distribution:
            return self.distribution.percentages
        return {}

    @property
    def vote_counts(self) -> Dict[int, int]:
        """Get vote counts (compatibility property)."""
        if self.distribution:
            return self.distribution.vote_counts
        return {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "mal_id": self.mal_id,
            "title": self.title,
            "url": self.url,
            "rank": self.rank,
            "score": self.score,
            "members": self.members,
            "distribution": self.distribution.to_dict() if self.distribution else None,
            "content_type": str(self.content_type),
            "is_sequel": self.is_sequel,
            "start_year": self.start_year,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnimeData":
        """Create from dictionary."""
        distribution = None
        if data.get("distribution"):
            distribution = ScoreDistribution.from_dict(data["distribution"])
        elif data.get("score_distribution") or data.get("vote_counts"):
            # Legacy format support
            distribution = ScoreDistribution(
                percentages={
                    int(k): v for k, v in data.get("score_distribution", {}).items()
                },
                vote_counts={int(k): v for k, v in data.get("vote_counts", {}).items()},
                total_votes=data.get("total_votes", 0),
            )

        content_type = ContentType.UNKNOWN
        if ct := data.get("content_type"):
            try:
                content_type = ContentType(ct)
            except ValueError:
                pass

        scraped_at = None
        if sat := data.get("scraped_at"):
            try:
                scraped_at = datetime.fromisoformat(sat)
            except ValueError:
                pass

        return cls(
            mal_id=data["mal_id"],
            title=data.get("title", ""),
            url=data.get("url", ""),
            rank=data.get("rank", 0),
            score=data.get("score", 0.0),
            members=data.get("members", 0),
            distribution=distribution,
            content_type=content_type,
            is_sequel=data.get("is_sequel", False),
            start_year=data.get("start_year", 0),
            scraped_at=scraped_at,
        )


@dataclass
class ContextualFactors:
    """
    Contextual factors for bombing analysis.

    These factors help adjust the bombing score based on
    the anime's characteristics.
    """

    anime_age_years: float = 0.0
    total_members: int = 0
    members_rank: int = 0
    score_rank: int = 0
    votes_to_members_ratio: float = 0.0
    popularity_tier: str = "unknown"
    content_type: ContentType = ContentType.UNKNOWN
    is_sequel: bool = False

    # Adjustment factors
    age_adjustment: float = 1.0
    popularity_adjustment: float = 1.0
    format_adjustment: float = 1.0

    def get_total_adjustment(self) -> float:
        """Calculate combined adjustment factor."""
        return self.age_adjustment * self.popularity_adjustment * self.format_adjustment


@dataclass
class BombingSeverity:
    """
    Detailed classification of bombing severity.

    Provides impact assessment and estimated fake votes.
    """

    level: SeverityLevel
    confidence: float
    impact_score: float
    estimated_fake_votes: int
    rating_impact: float
    description: str
    statistical_significance: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "level": str(self.level),
            "confidence": self.confidence,
            "impact_score": self.impact_score,
            "estimated_fake_votes": self.estimated_fake_votes,
            "rating_impact": self.rating_impact,
            "description": self.description,
            "statistical_significance": self.statistical_significance,
        }


@dataclass
class ReviewBombingMetrics:
    """
    Complete review bombing metrics for an anime.

    This is the main output of the bombing analysis.

    Attributes:
        mal_id: Anime ID.
        title: Anime title.
        ones_zscore: Z-score of ones percentage vs expected.
        distribution_effect_size: Cohen's d effect size.
        spike_ratio: Ratio of 1s to 2s votes.
        entropy_deficit: How much entropy is below expected.
        bimodality_coefficient: Bimodality measure (0-1).
        ones_percentage: Percentage of score 1 votes.
        tens_percentage: Percentage of score 10 votes.
        bombing_score: Composite bombing suspicion score (0-100).
        adjusted_score: Score after contextual adjustments.
        suspicion_level: Classification level.
        bombing_rank: Rank among analyzed anime.
        metric_breakdown: Individual metric contributions.
        z_scores: Z-scores for various metrics.
        anomaly_flags: List of detected anomalies.
        contextual_factors: Context for the analysis.
        severity: Severity assessment.
    """

    mal_id: int
    title: str

    # Core metrics
    ones_zscore: float
    distribution_effect_size: float
    spike_ratio: float
    entropy_deficit: float
    bimodality_coefficient: float

    # Distribution info
    ones_percentage: float
    tens_percentage: float

    # Scores
    bombing_score: float
    adjusted_score: float = 0.0

    # Classification
    suspicion_level: SuspicionLevel = SuspicionLevel.LOW
    bombing_rank: int = 0

    # Details
    metric_breakdown: Dict[str, float] = field(default_factory=dict)
    z_scores: Dict[str, float] = field(default_factory=dict)
    anomaly_flags: List[str] = field(default_factory=list)

    # Context
    contextual_factors: Optional[ContextualFactors] = None
    severity: Optional[BombingSeverity] = None

    # Legacy compatibility fields
    extreme_rating_ratio: float = 0.0
    low_score_anomaly: float = 0.0
    distribution_deviation: float = 0.0
    rating_mismatch: float = 0.0
    polarization_index: float = 0.0

    # Alias for backwards compatibility
    @property
    def suspicion_score(self) -> float:
        """Alias for bombing_score (backwards compatibility)."""
        return self.bombing_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "mal_id": self.mal_id,
            "title": self.title,
            "ones_zscore": self.ones_zscore,
            "distribution_effect_size": self.distribution_effect_size,
            "spike_ratio": self.spike_ratio,
            "entropy_deficit": self.entropy_deficit,
            "bimodality_coefficient": self.bimodality_coefficient,
            "ones_percentage": self.ones_percentage,
            "tens_percentage": self.tens_percentage,
            "bombing_score": self.bombing_score,
            "adjusted_score": self.adjusted_score,
            "suspicion_level": str(self.suspicion_level),
            "bombing_rank": self.bombing_rank,
            "metric_breakdown": self.metric_breakdown,
            # Only include non-empty z_scores to avoid empty placeholders (Fix E)
            **({"z_scores": self.z_scores} if self.z_scores else {}),
            "anomaly_flags": self.anomaly_flags,
        }

        # Legacy fields - include only when non-zero to avoid misleading placeholders (Fix E)
        if self.extreme_rating_ratio:
            result["extreme_rating_ratio"] = self.extreme_rating_ratio
        if self.low_score_anomaly:
            result["low_score_anomaly"] = self.low_score_anomaly
        if self.distribution_deviation:
            result["distribution_deviation"] = self.distribution_deviation
        if self.rating_mismatch:
            result["rating_mismatch"] = self.rating_mismatch
        if self.polarization_index:
            result["polarization_index"] = self.polarization_index

        if self.severity:
            result["severity"] = self.severity.to_dict()

        if self.contextual_factors:
            result["context"] = {
                "anime_age_years": self.contextual_factors.anime_age_years,
                "total_members": self.contextual_factors.total_members,
                "popularity_tier": self.contextual_factors.popularity_tier,
                "content_type": str(self.contextual_factors.content_type),
            }

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewBombingMetrics":
        """Create from dictionary."""
        suspicion_level = SuspicionLevel.LOW
        if sl := data.get("suspicion_level"):
            try:
                suspicion_level = SuspicionLevel(sl)
            except ValueError:
                pass

        return cls(
            mal_id=data["mal_id"],
            title=data.get("title", ""),
            ones_zscore=data.get("ones_zscore", 0.0),
            distribution_effect_size=data.get("distribution_effect_size", 0.0),
            spike_ratio=data.get("spike_ratio", 0.0),
            entropy_deficit=data.get("entropy_deficit", 0.0),
            bimodality_coefficient=data.get("bimodality_coefficient", 0.0),
            ones_percentage=data.get("ones_percentage", 0.0),
            tens_percentage=data.get("tens_percentage", 0.0),
            bombing_score=data.get("bombing_score", data.get("suspicion_score", 0.0)),
            adjusted_score=data.get("adjusted_score", 0.0),
            suspicion_level=suspicion_level,
            bombing_rank=data.get("bombing_rank", 0),
            metric_breakdown=data.get("metric_breakdown", {}),
            z_scores=data.get("z_scores", {}),
            anomaly_flags=data.get("anomaly_flags", []),
        )


@dataclass
class AnalysisSummary:
    """
    Summary statistics for a batch analysis.

    Provides aggregate information about all analyzed anime.

    Attributes:
        total_requested: Number of anime requested for analysis.
        total_analyzed: Number of anime successfully analyzed.
        total_failed: Number of anime that failed at any stage.
        total_skipped: Number skipped (e.g., insufficient votes).

        score_*: Statistics about bombing scores.
        ones_*: Statistics about ones percentages.

        critical_count/high_count/medium_count/low_count:
            Count by suspicion level (derived from bombing_score thresholds).

        suspicious_count: Count of medium + high + critical (score >= 35).
        highly_suspicious_count: Count of high + critical (score >= 55).
    """

    total_analyzed: int

    # Request tracking (Fix A/B)
    total_requested: int = 0
    total_failed: int = 0
    total_skipped: int = 0

    # Score statistics
    score_mean: float = 0.0
    score_median: float = 0.0
    score_std: float = 0.0
    score_min: float = 0.0
    score_max: float = 0.0

    # Ones percentage statistics
    ones_mean: float = 0.0
    ones_median: float = 0.0
    ones_max: float = 0.0

    # Level distribution (Fix C/D - derived from bombing_score thresholds)
    critical_count: int = 0  # bombing_score >= 75
    high_count: int = 0  # bombing_score >= 55 and < 75
    medium_count: int = 0  # bombing_score >= 35 and < 55
    low_count: int = 0  # bombing_score < 35

    @property
    def suspicious_count(self) -> int:
        """Count of anime with medium, high, or critical suspicion (score >= 35)."""
        return self.medium_count + self.high_count + self.critical_count

    @property
    def highly_suspicious_count(self) -> int:
        """Count of anime with high or critical suspicion (score >= 55)."""
        return self.high_count + self.critical_count

    @property
    def count_by_level(self) -> Dict[str, int]:
        """Level distribution as a dictionary."""
        return {
            "critical": self.critical_count,
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_requested": self.total_requested,
            "total_analyzed": self.total_analyzed,
            "total_failed": self.total_failed,
            "total_skipped": self.total_skipped,
            "bombing_score": {
                "mean": self.score_mean,
                "median": self.score_median,
                "std": self.score_std,
                "min": self.score_min,
                "max": self.score_max,
            },
            "ones_percentage": {
                "mean": self.ones_mean,
                "median": self.ones_median,
                "max": self.ones_max,
            },
            "count_by_level": self.count_by_level,
            "suspicious_count": self.suspicious_count,
            "highly_suspicious_count": self.highly_suspicious_count,
        }
