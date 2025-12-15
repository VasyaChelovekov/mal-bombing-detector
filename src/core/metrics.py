"""
Core metrics calculation for review bombing detection.

This module provides the main metrics calculator that analyzes
anime score distributions to detect potential review bombing.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from ..utils.config import get_config
from ..utils.logging import get_logger
from .models import (
    AnimeData,
    BombingSeverity,
    ContentType,
    ContextualFactors,
    ReviewBombingMetrics,
    SeverityLevel,
    SuspicionLevel,
)
from .statistics import (
    DistributionStatistics,
    EffectSizeCalculator,
    ZScoreCalculator,
    get_expected_distribution,
)


logger = get_logger(__name__)


class MetricsCalculator:
    """
    Calculator for review bombing metrics.
    
    Analyzes anime score distributions to detect statistical
    anomalies that may indicate coordinated vote manipulation.
    
    The calculator uses multiple metrics:
    - Z-score of ones percentage
    - Spike ratio (ones/twos)
    - Distribution effect size
    - Entropy deficit
    - Bimodality coefficient
    
    Example:
        >>> calculator = MetricsCalculator()
        >>> metrics = calculator.calculate(anime_data)
        >>> print(f"Bombing score: {metrics.bombing_score}")
    """
    
    def __init__(self):
        """Initialize the metrics calculator."""
        self.config = get_config()
        self.stats = DistributionStatistics()
        self.zscore_calc = ZScoreCalculator()
        self.effect_calc = EffectSizeCalculator()
    
    def calculate(self, anime: AnimeData) -> ReviewBombingMetrics:
        """
        Calculate bombing metrics for an anime.
        
        Args:
            anime: Anime data with score distribution.
        
        Returns:
            ReviewBombingMetrics with all calculated values.
        """
        if anime.distribution is None:
            raise ValueError(f"No distribution data for anime {anime.mal_id}")
        
        distribution = anime.distribution.percentages
        vote_counts = anime.distribution.vote_counts
        total_votes = anime.distribution.total_votes
        
        ones_pct = distribution.get(1, 0)
        tens_pct = distribution.get(10, 0)
        
        # Calculate core metrics
        ones_zscore = self.zscore_calc.calculate_ones_zscore(ones_pct, anime.score)
        spike_ratio = self.effect_calc.calculate_spike_ratio(distribution)
        effect_size = self._calculate_effect_size(distribution, anime.score)
        entropy_deficit = self.stats.calculate_entropy_deficit(distribution)
        
        # Bimodality
        is_bimodal, bimodality = self.stats.detect_bimodality(distribution)
        
        # Calculate composite score
        metric_scores = self._calculate_metric_scores(
            ones_zscore, spike_ratio, effect_size, entropy_deficit, 
            bimodality, is_bimodal
        )
        
        bombing_score = sum(metric_scores.values())
        bombing_score = min(100, max(0, bombing_score))
        
        # Contextual factors
        context = self._calculate_context(anime, total_votes)
        
        # Adjusted score
        adjusted_score = bombing_score * context.get_total_adjustment()
        adjusted_score = min(100, max(0, adjusted_score))
        
        # Classification (with z-score and spike ratio overrides for extreme cases)
        suspicion_level = self._classify_level(
            bombing_score, ones_zscore, ones_pct, spike_ratio
        )
        
        # Severity
        severity = self._calculate_severity(
            bombing_score, ones_pct, total_votes, anime.score, 
            bimodality, ones_zscore
        )
        
        # Anomaly flags
        anomaly_flags = self._detect_anomaly_flags(
            ones_zscore, spike_ratio, effect_size, entropy_deficit,
            is_bimodal, bimodality
        )
        
        # Polarization for visualization
        polarization = self.stats.calculate_polarization_index(distribution)
        
        return ReviewBombingMetrics(
            mal_id=anime.mal_id,
            title=anime.title,
            ones_zscore=round(ones_zscore, 2),
            distribution_effect_size=round(effect_size, 3),
            spike_ratio=round(spike_ratio, 2),
            entropy_deficit=round(entropy_deficit, 3),
            bimodality_coefficient=round(bimodality, 3),
            ones_percentage=round(ones_pct, 2),
            tens_percentage=round(tens_pct, 2),
            bombing_score=round(bombing_score, 2),
            adjusted_score=round(adjusted_score, 2),
            suspicion_level=suspicion_level,
            metric_breakdown={k: round(v, 2) for k, v in metric_scores.items()},
            contextual_factors=context,
            severity=severity,
            anomaly_flags=anomaly_flags,
            # Legacy compatibility
            low_score_anomaly=round(max(0, ones_pct - 0.5), 2),
            distribution_deviation=round(effect_size * 100, 2),
            polarization_index=round(polarization, 2),
        )
    
    def _calculate_effect_size(
        self,
        distribution: Dict[int, float],
        anime_score: float,
    ) -> float:
        """Calculate effect size of distribution deviation."""
        expected = get_expected_distribution(anime_score)
        return self.effect_calc.calculate_cohens_d(distribution, expected)
    
    def _calculate_metric_scores(
        self,
        ones_zscore: float,
        spike_ratio: float,
        effect_size: float,
        entropy_deficit: float,
        bimodality: float,
        is_bimodal: bool,
    ) -> Dict[str, float]:
        """Calculate weighted scores for each metric."""
        weights = self.config.analysis.metric_weights
        
        # Normalize metrics to 0-100 scale
        ones_score = min(100, ones_zscore * 25)
        spike_score = min(100, max(0, (spike_ratio - 1.5) * 20))
        effect_score = min(100, effect_size * 80)
        entropy_score = min(100, entropy_deficit * 300)
        bimodality_score = bimodality * 100 if is_bimodal else bimodality * 30
        
        return {
            'ONES_Z': ones_score * weights.ones_zscore,
            'SPIKE': spike_score * weights.spike_anomaly,
            'EFFECT': effect_score * weights.distribution_effect,
            'ENTROPY': entropy_score * weights.entropy_deficit,
            'BIMODAL': bimodality_score * weights.bimodality,
        }
    
    def _calculate_context(
        self,
        anime: AnimeData,
        total_votes: int,
    ) -> ContextualFactors:
        """Calculate contextual adjustment factors."""
        factors = ContextualFactors()
        factors.content_type = anime.content_type
        factors.is_sequel = anime.is_sequel
        
        # Age
        if anime.start_year > 0:
            factors.anime_age_years = datetime.now().year - anime.start_year
        
        # Popularity
        factors.total_members = anime.members
        
        if anime.members > 0:
            factors.votes_to_members_ratio = total_votes / anime.members
        
        # Determine popularity tier
        if anime.rank > 0:
            if anime.rank <= 50:
                factors.popularity_tier = "mega_popular"
            elif anime.rank <= 200:
                factors.popularity_tier = "very_popular"
            elif anime.rank <= 500:
                factors.popularity_tier = "popular"
            else:
                factors.popularity_tier = "moderate"
        
        # Age adjustment
        age_config = self.config.analysis
        if factors.anime_age_years > age_config.age_old_threshold_years:
            factors.age_adjustment = age_config.age_old_factor
        else:
            factors.age_adjustment = age_config.age_default_factor
        
        # Format adjustment
        format_adj = self.config.analysis.format_adjustments
        if anime.content_type in (ContentType.MOVIE, ContentType.OVA, ContentType.SPECIAL):
            factors.format_adjustment = format_adj.movie
        elif anime.is_sequel:
            factors.format_adjustment = format_adj.sequel
        else:
            factors.format_adjustment = format_adj.default
        
        return factors
    
    def _classify_level(
        self,
        score: float,
        ones_zscore: float = 0.0,
        ones_pct: float = 0.0,
        spike_ratio: float = 0.0,
    ) -> SuspicionLevel:
        """
        Classify bombing score into suspicion level.
        
        Applies overrides for extreme statistical anomalies
        that may not be captured by the composite score alone.
        
        Args:
            score: Composite bombing score.
            ones_zscore: Z-score of ones percentage.
            ones_pct: Actual ones percentage.
            spike_ratio: Ratio of 1-votes to 2-votes.
        
        Returns:
            Suspicion level classification.
        """
        thresholds = self.config.analysis.suspicion_thresholds
        
        # Z-score override: extreme statistical anomalies
        # For highly rated anime (elite/excellent), high ones% is very suspicious
        # Z-score > 10 means the ones% is 10+ standard deviations above expected
        if ones_zscore >= 15:
            return SuspicionLevel.CRITICAL
        elif ones_zscore >= 10:
            return SuspicionLevel.HIGH
        elif ones_zscore >= 6 and ones_pct >= 3.0:
            # High z-score + substantial ones percentage = suspicious
            return SuspicionLevel.HIGH
        
        # Spike ratio override: extreme 1:2 vote imbalance
        # Natural distributions have 1s and 2s in similar proportions
        # Ratio > 10 is extremely unnatural and indicates coordinated 1-bombing
        if spike_ratio >= 10.0:
            return SuspicionLevel.HIGH
        elif spike_ratio >= 6.0 and ones_pct >= 1.5:
            # High spike ratio + notable ones = suspicious
            return SuspicionLevel.MEDIUM
        
        # Standard threshold-based classification
        if score >= thresholds.critical:
            return SuspicionLevel.CRITICAL
        elif score >= thresholds.high:
            return SuspicionLevel.HIGH
        elif score >= thresholds.medium:
            return SuspicionLevel.MEDIUM
        else:
            return SuspicionLevel.LOW
    
    def _calculate_severity(
        self,
        bombing_score: float,
        ones_pct: float,
        total_votes: int,
        anime_score: float,
        bimodality: float,
        ones_zscore: float,
    ) -> BombingSeverity:
        """Calculate bombing severity assessment."""
        # Statistical significance
        if ones_zscore >= 2.58:
            p_value = 0.01
        elif ones_zscore >= 1.96:
            p_value = 0.05
        elif ones_zscore >= 1.65:
            p_value = 0.10
        else:
            p_value = 0.50
        
        # Estimate fake votes
        category = self.zscore_calc.get_rating_category(anime_score)
        expected = self.config.analysis.expected_ones_by_rating.get(category)
        
        max_natural = expected.max_natural if expected else 2.0
        excess_ones_pct = max(0, ones_pct - max_natural)
        estimated_fake_votes = int((excess_ones_pct / 100) * total_votes)
        
        # Rating impact
        if total_votes > 0:
            rating_impact = (estimated_fake_votes * (anime_score - 1)) / total_votes
        else:
            rating_impact = 0.0
        
        # Determine level
        if bombing_score >= 75:
            level = SeverityLevel.EXTREME
            description = "Statistically significant anomaly. High probability of organized attack."
        elif bombing_score >= 55:
            level = SeverityLevel.SEVERE
            description = "Significant deviation from norm. Likely coordinated bombing."
        elif bombing_score >= 35:
            level = SeverityLevel.MODERATE
            description = "Notable deviation. Could be attack or natural polarization."
        elif bombing_score >= 20:
            level = SeverityLevel.LIGHT
            description = "Minor deviation within natural variation."
        else:
            level = SeverityLevel.NONE
            description = "Distribution matches expected pattern."
        
        # Confidence
        confidence = min(1.0, 0.3 + bombing_score / 100 + (0.2 if p_value < 0.05 else 0))
        
        return BombingSeverity(
            level=level,
            confidence=round(confidence, 2),
            impact_score=round(bombing_score, 2),
            estimated_fake_votes=estimated_fake_votes,
            rating_impact=round(rating_impact, 3),
            description=description,
            statistical_significance=1 - p_value,
        )
    
    def _detect_anomaly_flags(
        self,
        ones_zscore: float,
        spike_ratio: float,
        effect_size: float,
        entropy_deficit: float,
        is_bimodal: bool,
        bimodality: float,
    ) -> List[str]:
        """Detect anomaly flags based on thresholds."""
        flags = []
        thresholds = self.config.analysis.statistical_thresholds
        
        # Z-score
        if ones_zscore >= thresholds.ones_zscore_extreme:
            flags.append("EXTREME_ONES_ANOMALY")
        elif ones_zscore >= thresholds.ones_zscore_significant:
            flags.append("SIGNIFICANT_ONES_ANOMALY")
        
        # Spike ratio
        if spike_ratio >= thresholds.spike_ratio_extreme:
            flags.append("EXTREME_SPIKE_PATTERN")
        elif spike_ratio >= thresholds.spike_ratio_elevated:
            flags.append("ELEVATED_SPIKE_PATTERN")
        
        # Bimodality
        if is_bimodal and bimodality >= thresholds.bimodality_confirmed:
            flags.append("CONFIRMED_BIMODALITY")
        elif bimodality >= thresholds.bimodality_possible:
            flags.append("POSSIBLE_BIMODALITY")
        
        # Effect size
        if effect_size >= thresholds.effect_size_large:
            flags.append("LARGE_DISTRIBUTION_EFFECT")
        elif effect_size >= thresholds.effect_size_medium:
            flags.append("MEDIUM_DISTRIBUTION_EFFECT")
        
        # Entropy
        if entropy_deficit >= thresholds.entropy_deficit_warning:
            flags.append("LOW_ENTROPY_WARNING")
        
        return flags
    
    def rank_by_bombing(
        self,
        metrics_list: List[ReviewBombingMetrics],
    ) -> List[ReviewBombingMetrics]:
        """
        Rank anime by bombing score.
        
        Args:
            metrics_list: List of metrics to rank.
        
        Returns:
            Sorted list with assigned ranks.
        """
        sorted_metrics = sorted(
            metrics_list,
            key=lambda x: x.bombing_score,
            reverse=True,
        )
        
        for i, metrics in enumerate(sorted_metrics, 1):
            metrics.bombing_rank = i
        
        return sorted_metrics
