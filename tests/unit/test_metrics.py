"""
Unit tests for metrics module.
"""

import pytest

from src.core.models import AnimeData, ScoreDistribution, SeverityLevel, SuspicionLevel
from src.core.metrics import MetricsCalculator


class TestMetricsCalculator:
    """Tests for MetricsCalculator class."""

    @pytest.fixture
    def calculator(self):
        """Create a MetricsCalculator instance."""
        return MetricsCalculator()

    @pytest.fixture
    def normal_anime(self, normal_score_distribution):
        """Create anime with normal distribution."""
        total = sum(normal_score_distribution.values())
        percentages = {
            k: (v / total * 100) for k, v in normal_score_distribution.items()
        }

        dist = ScoreDistribution(
            vote_counts=normal_score_distribution,
            percentages=percentages,
            total_votes=total,
        )

        return AnimeData(
            mal_id=12345,
            title="Normal Anime",
            score=8.5,
            members=100000,
            url="https://myanimelist.net/anime/12345",
            rank=10,
            distribution=dist,
        )

    @pytest.fixture
    def bombed_anime(self, bombed_score_distribution):
        """Create anime with bombed distribution."""
        total = sum(bombed_score_distribution.values())
        percentages = {
            k: (v / total * 100) for k, v in bombed_score_distribution.items()
        }

        dist = ScoreDistribution(
            vote_counts=bombed_score_distribution,
            percentages=percentages,
            total_votes=total,
        )

        return AnimeData(
            mal_id=67890,
            title="Bombed Anime",
            score=7.5,
            members=50000,
            url="https://myanimelist.net/anime/67890",
            rank=50,
            distribution=dist,
        )

    def test_calculate_returns_metrics(self, calculator, normal_anime):
        """Test that calculate returns ReviewBombingMetrics."""
        metrics = calculator.calculate(normal_anime)

        assert metrics is not None
        assert metrics.mal_id == normal_anime.mal_id
        assert metrics.title == normal_anime.title

    def test_calculate_normal_distribution(self, calculator, normal_anime):
        """Test metrics for normal distribution."""
        metrics = calculator.calculate(normal_anime)

        # Normal distribution should have low bombing score
        assert metrics.bombing_score < 50
        assert metrics.suspicion_level in [SuspicionLevel.LOW, SuspicionLevel.MEDIUM]

    def test_calculate_bombed_distribution(self, calculator, bombed_anime):
        """Test metrics for bombed distribution."""
        metrics = calculator.calculate(bombed_anime)

        # Bombed distribution should have high bombing score
        assert metrics.bombing_score > 30  # Should show some elevation
        assert metrics.ones_percentage > 20  # Should have high ones %

    def test_ones_percentage_calculation(self, calculator, bombed_anime):
        """Test ones percentage is calculated correctly."""
        metrics = calculator.calculate(bombed_anime)

        # 5000 ones out of total votes
        total = sum(bombed_anime.distribution.vote_counts.values())
        expected_ones_pct = 5000 / total * 100

        assert metrics.ones_percentage == pytest.approx(expected_ones_pct, rel=0.1)

    def test_tens_percentage_calculation(self, calculator, bombed_anime):
        """Test tens percentage is calculated correctly."""
        metrics = calculator.calculate(bombed_anime)

        # 4000 tens out of total votes
        total = sum(bombed_anime.distribution.vote_counts.values())
        expected_tens_pct = 4000 / total * 100

        assert metrics.tens_percentage == pytest.approx(expected_tens_pct, rel=0.1)

    def test_core_metrics_populated(self, calculator, normal_anime):
        """Test that core metrics are populated."""
        metrics = calculator.calculate(normal_anime)

        # All core metrics should be present
        assert hasattr(metrics, "ones_zscore")
        assert hasattr(metrics, "spike_ratio")
        assert hasattr(metrics, "distribution_effect_size")
        assert hasattr(metrics, "entropy_deficit")
        assert hasattr(metrics, "bimodality_coefficient")

    def test_bombing_score_in_range(self, calculator, normal_anime):
        """Test bombing score is within valid range."""
        metrics = calculator.calculate(normal_anime)

        # Score should be 0-100
        assert 0 <= metrics.bombing_score <= 100

    def test_missing_distribution_raises_error(self, calculator):
        """Test that missing distribution raises error."""
        anime = AnimeData(mal_id=1, title="No Distribution", score=8.0, url="")

        with pytest.raises(ValueError):
            calculator.calculate(anime)


class TestMetricsCalculatorRanking:
    """Tests for ranking functionality."""

    @pytest.fixture
    def calculator(self):
        return MetricsCalculator()

    def test_rank_by_bombing_orders_correctly(
        self, calculator, normal_score_distribution, bombed_score_distribution
    ):
        """Test that ranking orders by bombing score."""
        # Create anime with different distributions
        normal_total = sum(normal_score_distribution.values())
        normal_pct = {
            k: (v / normal_total * 100) for k, v in normal_score_distribution.items()
        }

        bombed_total = sum(bombed_score_distribution.values())
        bombed_pct = {
            k: (v / bombed_total * 100) for k, v in bombed_score_distribution.items()
        }

        normal_anime = AnimeData(
            mal_id=1,
            title="Normal",
            score=8.5,
            url="",
            distribution=ScoreDistribution(
                vote_counts=normal_score_distribution,
                percentages=normal_pct,
                total_votes=normal_total,
            ),
        )

        bombed_anime = AnimeData(
            mal_id=2,
            title="Bombed",
            score=7.5,
            url="",
            distribution=ScoreDistribution(
                vote_counts=bombed_score_distribution,
                percentages=bombed_pct,
                total_votes=bombed_total,
            ),
        )

        metrics_list = [
            calculator.calculate(normal_anime),
            calculator.calculate(bombed_anime),
        ]

        ranked = calculator.rank_by_bombing(metrics_list)

        # Bombed should rank higher (lower rank number = more suspicious)
        bombed_rank = next(m.bombing_rank for m in ranked if m.mal_id == 2)
        normal_rank = next(m.bombing_rank for m in ranked if m.mal_id == 1)

        assert bombed_rank < normal_rank


class TestSuspicionLevelEnum:
    """Tests for SuspicionLevel enum."""

    def test_levels_exist(self):
        """Test all suspicion levels exist."""
        assert SuspicionLevel.CRITICAL.value == "critical"
        assert SuspicionLevel.HIGH.value == "high"
        assert SuspicionLevel.MEDIUM.value == "medium"
        assert SuspicionLevel.LOW.value == "low"


class TestSeverityLevelEnum:
    """Tests for SeverityLevel enum."""

    def test_severities_exist(self):
        """Test all severity levels exist."""
        assert SeverityLevel.EXTREME.value == "extreme"
        assert SeverityLevel.SEVERE.value == "severe"
        assert SeverityLevel.MODERATE.value == "moderate"
        assert SeverityLevel.LIGHT.value == "light"
        assert SeverityLevel.NONE.value == "none"
