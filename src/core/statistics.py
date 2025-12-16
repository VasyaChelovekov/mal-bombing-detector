"""
Statistical utilities for review bombing analysis.

This module provides statistical functions used in bombing detection:
- Distribution analysis
- Z-score calculations
- Effect size measurements
- Entropy calculations
- Bimodality detection
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

import numpy as np
from scipy import stats as scipy_stats

from ..utils.config import get_config


class DistributionStatistics:
    """
    Statistical analysis of score distributions.

    Provides methods for analyzing anime score distributions
    and detecting anomalies that may indicate review bombing.
    """

    def __init__(self):
        """Initialize with configuration."""
        self.config = get_config()

    @staticmethod
    def calculate_mean(distribution: Dict[int, float]) -> float:
        """
        Calculate weighted mean of distribution.

        Args:
            distribution: Score percentages (1-10 -> percentage).

        Returns:
            Weighted mean score.
        """
        total = sum(distribution.values())
        if total == 0:
            return 0.0

        weighted_sum = sum(score * pct for score, pct in distribution.items())
        return weighted_sum / total

    @staticmethod
    def calculate_std(distribution: Dict[int, float]) -> float:
        """
        Calculate standard deviation of distribution.

        Args:
            distribution: Score percentages.

        Returns:
            Standard deviation.
        """
        mean = DistributionStatistics.calculate_mean(distribution)
        total = sum(distribution.values())

        if total == 0:
            return 0.0

        variance = (
            sum(pct * (score - mean) ** 2 for score, pct in distribution.items())
            / total
        )

        return math.sqrt(variance)

    @staticmethod
    def calculate_median(distribution: Dict[int, float]) -> float:
        """
        Calculate median score from distribution.

        Args:
            distribution: Score percentages.

        Returns:
            Median score.
        """
        cumulative = 0.0

        for score in sorted(distribution.keys()):
            cumulative += distribution.get(score, 0)
            if cumulative >= 50.0:
                return float(score)

        return 5.0  # Default median

    @staticmethod
    def calculate_entropy(distribution: Dict[int, float]) -> float:
        """
        Calculate Shannon entropy of distribution.

        Higher entropy = more uniform distribution.
        Lower entropy = more concentrated distribution.

        Args:
            distribution: Score percentages.

        Returns:
            Entropy value (0 to log2(10) ≈ 3.32).
        """
        probabilities = []
        total = sum(distribution.values())

        if total == 0:
            return 0.0

        for score in range(1, 11):
            p = distribution.get(score, 0) / total
            if p > 0:
                probabilities.append(p)

        if not probabilities:
            return 0.0

        # Normalize
        prob_sum = sum(probabilities)
        probabilities = [p / prob_sum for p in probabilities]

        # Shannon entropy
        entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)
        return entropy

    @staticmethod
    def calculate_normalized_entropy(distribution: Dict[int, float]) -> float:
        """
        Calculate normalized entropy (0 to 1).

        Args:
            distribution: Score percentages.

        Returns:
            Normalized entropy (0 = concentrated, 1 = uniform).
        """
        max_entropy = math.log2(10)  # Maximum for 10 categories
        entropy = DistributionStatistics.calculate_entropy(distribution)
        return entropy / max_entropy if max_entropy > 0 else 0.0

    def calculate_entropy_deficit(
        self,
        distribution: Dict[int, float],
        expected_entropy: float = 0.68,
    ) -> float:
        """
        Calculate entropy deficit relative to expected.

        Args:
            distribution: Score percentages.
            expected_entropy: Expected normalized entropy for top anime.

        Returns:
            Entropy deficit (how much lower than expected).
        """
        normalized = self.calculate_normalized_entropy(distribution)
        return max(0.0, expected_entropy - normalized)

    @staticmethod
    def calculate_skewness(distribution: Dict[int, float]) -> float:
        """
        Calculate skewness of distribution.

        Negative skew = tail on left (more low scores).
        Positive skew = tail on right (more high scores).

        Args:
            distribution: Score percentages.

        Returns:
            Skewness coefficient.
        """
        mean = DistributionStatistics.calculate_mean(distribution)
        std = DistributionStatistics.calculate_std(distribution)

        if std == 0:
            return 0.0

        total = sum(distribution.values())
        if total == 0:
            return 0.0

        skew = (
            sum(
                pct * ((score - mean) / std) ** 3 for score, pct in distribution.items()
            )
            / total
        )

        return skew

    @staticmethod
    def calculate_kurtosis(distribution: Dict[int, float]) -> float:
        """
        Calculate kurtosis of distribution.

        High kurtosis = heavy tails (more extreme values).
        Low kurtosis = light tails.

        Args:
            distribution: Score percentages.

        Returns:
            Kurtosis (excess kurtosis, normal = 0).
        """
        mean = DistributionStatistics.calculate_mean(distribution)
        std = DistributionStatistics.calculate_std(distribution)

        if std == 0:
            return 0.0

        total = sum(distribution.values())
        if total == 0:
            return 0.0

        kurt = (
            sum(
                pct * ((score - mean) / std) ** 4 for score, pct in distribution.items()
            )
            / total
        )

        # Excess kurtosis (subtract 3 for normal distribution)
        return kurt - 3.0

    @staticmethod
    def calculate_bimodality_coefficient(distribution: Dict[int, float]) -> float:
        """
        Calculate bimodality coefficient.

        Uses Sarle's bimodality coefficient:
        BC = (skewness² + 1) / (kurtosis + 3 * (n-1)²/(n-2)(n-3))

        Simplified version: BC > 0.555 suggests bimodality.

        Args:
            distribution: Score percentages.

        Returns:
            Bimodality coefficient (0 to ~1).
        """
        skewness = DistributionStatistics.calculate_skewness(distribution)
        kurtosis = DistributionStatistics.calculate_kurtosis(distribution)

        # Sarle's bimodality coefficient (simplified)
        numerator = skewness**2 + 1
        denominator = kurtosis + 3

        if denominator <= 0:
            return 0.0

        bc = numerator / denominator
        return min(1.0, bc)

    @staticmethod
    def detect_bimodality(
        distribution: Dict[int, float],
        threshold: float = 0.555,
    ) -> Tuple[bool, float]:
        """
        Detect if distribution is bimodal.

        Args:
            distribution: Score percentages.
            threshold: Bimodality coefficient threshold.

        Returns:
            Tuple of (is_bimodal, coefficient).
        """
        bc = DistributionStatistics.calculate_bimodality_coefficient(distribution)
        return bc > threshold, bc

    @staticmethod
    def calculate_polarization_index(distribution: Dict[int, float]) -> float:
        """
        Calculate polarization index.

        Measures the concentration of votes at extremes (1s and 10s)
        versus middle scores.

        Args:
            distribution: Score percentages.

        Returns:
            Polarization index (0 to 100).
        """
        extreme = distribution.get(1, 0) + distribution.get(10, 0)
        middle = sum(distribution.get(s, 0) for s in range(4, 8))

        total = extreme + middle
        if total == 0:
            return 0.0

        # Normalize to 0-100 scale
        return min(100.0, (extreme / total) * 100)


class ZScoreCalculator:
    """
    Z-score calculations for anomaly detection.

    Compares observed values to expected distributions
    to detect statistically significant deviations.
    """

    def __init__(self):
        """Initialize with configuration."""
        self.config = get_config()

    def get_rating_category(self, score: float) -> str:
        """
        Get rating category for a score.

        Args:
            score: Anime score (1-10).

        Returns:
            Category name (elite, excellent, great, good, average).
        """
        if score >= 9.0:
            return "elite"
        elif score >= 8.5:
            return "excellent"
        elif score >= 8.0:
            return "great"
        elif score >= 7.5:
            return "good"
        else:
            return "average"

    def calculate_ones_zscore(
        self,
        ones_percentage: float,
        anime_score: float,
    ) -> float:
        """
        Calculate Z-score of ones percentage.

        Compares observed ones percentage to expected for the
        anime's rating category.

        Args:
            ones_percentage: Observed percentage of score 1 votes.
            anime_score: Anime's average score.

        Returns:
            Z-score (positive = above expected).
        """
        category = self.get_rating_category(anime_score)
        expected = self.config.analysis.expected_ones_by_rating.get(category)

        if expected is None:
            # Use 'good' as default
            expected = self.config.analysis.expected_ones_by_rating.get("good")
            if expected is None:
                return 0.0

        mean = expected.mean
        std = expected.std

        if std == 0:
            return 0.0

        zscore = (ones_percentage - mean) / std
        return max(0.0, zscore)  # Only positive deviations (excess ones)

    @staticmethod
    def zscore_to_pvalue(zscore: float, one_tailed: bool = True) -> float:
        """
        Convert Z-score to p-value.

        Args:
            zscore: Z-score value.
            one_tailed: Whether to use one-tailed test.

        Returns:
            P-value.
        """
        if one_tailed:
            return 1 - scipy_stats.norm.cdf(zscore)
        else:
            return 2 * (1 - scipy_stats.norm.cdf(abs(zscore)))

    @staticmethod
    def pvalue_to_significance(pvalue: float) -> str:
        """
        Convert p-value to significance level.

        Args:
            pvalue: P-value.

        Returns:
            Significance level description.
        """
        if pvalue < 0.001:
            return "highly_significant"
        elif pvalue < 0.01:
            return "very_significant"
        elif pvalue < 0.05:
            return "significant"
        elif pvalue < 0.10:
            return "marginally_significant"
        else:
            return "not_significant"


class EffectSizeCalculator:
    """
    Effect size calculations for distribution comparisons.

    Effect sizes measure the magnitude of differences,
    independent of sample size.
    """

    @staticmethod
    def calculate_cohens_d(
        observed: Dict[int, float],
        expected: Dict[int, float],
    ) -> float:
        """
        Calculate distribution effect size.

        Measures the standardized difference between
        observed and expected distributions using RMSE
        normalized by expected standard deviation.

        Note: Traditional Cohen's d (mean_diff/std) doesn't work
        for percentage distributions because both sum to 100%,
        making mean difference always 0.

        Args:
            observed: Observed distribution (percentages).
            expected: Expected distribution (percentages).

        Returns:
            Effect size (0.2=small, 0.5=medium, 0.8=large).
        """
        differences = []

        for score in range(1, 11):
            obs = observed.get(score, 0)
            exp = expected.get(score, 0)
            differences.append(obs - exp)

        if not differences:
            return 0.0

        # Use RMSE (Root Mean Square Error) normalized by expected std
        # This measures the magnitude of deviations, not just mean
        rmse = np.sqrt(np.mean(np.square(differences)))
        expected_std = np.std(list(expected.values()))

        if expected_std == 0:
            return rmse / 10.0  # Normalize by max possible

        # Normalize RMSE by expected std to get effect size
        # Scale factor to align with Cohen's d interpretation
        return rmse / expected_std

    @staticmethod
    def interpret_cohens_d(d: float) -> str:
        """
        Interpret Cohen's d value.

        Args:
            d: Cohen's d value.

        Returns:
            Interpretation (negligible, small, medium, large).
        """
        if d < 0.2:
            return "negligible"
        elif d < 0.5:
            return "small"
        elif d < 0.8:
            return "medium"
        else:
            return "large"

    @staticmethod
    def calculate_spike_ratio(distribution: Dict[int, float]) -> float:
        """
        Calculate spike ratio (ones to twos).

        In natural distributions, ones/twos ≈ 1.0-2.0.
        In bombing scenarios, ones/twos >> 3.0.

        Args:
            distribution: Score percentages.

        Returns:
            Spike ratio.
        """
        ones = distribution.get(1, 0)
        twos = distribution.get(2, 0)

        if twos < 0.1:
            return ones * 5 if ones > 0 else 0.0

        return ones / twos


def get_expected_distribution(score: float) -> Dict[int, float]:
    """
    Generate expected distribution for a given score.

    Creates a theoretical "natural" distribution for an anime
    with the given average score, assuming no bombing.

    Args:
        score: Anime average score.

    Returns:
        Expected percentage distribution.
    """
    # Approximate expected distribution based on score
    # Higher scored anime have more votes concentrated at high scores

    if score >= 9.0:
        # Elite tier - very concentrated at top
        return {
            1: 0.4,
            2: 0.3,
            3: 0.5,
            4: 1.0,
            5: 2.0,
            6: 5.0,
            7: 12.0,
            8: 25.0,
            9: 30.0,
            10: 23.8,
        }
    elif score >= 8.5:
        # Excellent tier
        return {
            1: 0.7,
            2: 0.5,
            3: 0.8,
            4: 1.5,
            5: 3.0,
            6: 7.0,
            7: 15.0,
            8: 28.0,
            9: 27.0,
            10: 16.5,
        }
    elif score >= 8.0:
        # Great tier
        return {
            1: 1.2,
            2: 0.8,
            3: 1.2,
            4: 2.5,
            5: 5.0,
            6: 10.0,
            7: 20.0,
            8: 30.0,
            9: 20.0,
            10: 9.3,
        }
    elif score >= 7.5:
        # Good tier
        return {
            1: 2.0,
            2: 1.5,
            3: 2.0,
            4: 4.0,
            5: 8.0,
            6: 15.0,
            7: 25.0,
            8: 25.0,
            9: 12.0,
            10: 5.5,
        }
    else:
        # Average and below
        return {
            1: 4.0,
            2: 3.0,
            3: 4.0,
            4: 7.0,
            5: 12.0,
            6: 20.0,
            7: 25.0,
            8: 15.0,
            9: 7.0,
            10: 3.0,
        }
