"""
Unit tests for bombing score adjustments (Phase 1 improvements).

Tests verify:
1. Minimum ones_pct thresholds for suspicion levels
2. Popularity discount for effect_size
3. Spike ratio damping at low ones_pct
"""

import pytest

from src.core.metrics import MetricsCalculator
from src.core.models import AnimeData, ScoreDistribution, SuspicionLevel


class TestSuspicionLevelThresholds:
    """Tests for minimum ones_pct enforcement on suspicion levels."""

    @pytest.fixture
    def calculator(self):
        """Create a metrics calculator instance."""
        return MetricsCalculator()

    def test_critical_requires_min_ones_pct(self, calculator):
        """CRITICAL level requires ones_pct >= 2.0%."""
        # High score but low ones_pct should downgrade to HIGH
        level = calculator._classify_level(
            score=80.0,  # Above CRITICAL threshold
            ones_pct=1.5,  # Below min_ones_for_critical (2.0)
        )
        assert level == SuspicionLevel.HIGH

    def test_critical_with_sufficient_ones_pct(self, calculator):
        """CRITICAL level allowed when ones_pct >= 2.0%."""
        level = calculator._classify_level(
            score=80.0,
            ones_pct=2.5,  # Above min_ones_for_critical
        )
        assert level == SuspicionLevel.CRITICAL

    def test_high_requires_min_ones_pct(self, calculator):
        """HIGH level requires ones_pct >= 1.5%."""
        # Score in HIGH range but low ones_pct should downgrade to MEDIUM
        level = calculator._classify_level(
            score=60.0,  # Above HIGH threshold
            ones_pct=1.0,  # Below min_ones_for_high (1.5)
        )
        assert level == SuspicionLevel.MEDIUM

    def test_high_with_sufficient_ones_pct(self, calculator):
        """HIGH level allowed when ones_pct >= 1.5%."""
        level = calculator._classify_level(
            score=60.0,
            ones_pct=1.8,  # Above min_ones_for_high
        )
        assert level == SuspicionLevel.HIGH

    def test_medium_no_ones_requirement(self, calculator):
        """MEDIUM level has no ones_pct requirement."""
        level = calculator._classify_level(
            score=40.0,  # Above MEDIUM threshold
            ones_pct=0.5,  # Low ones_pct
        )
        assert level == SuspicionLevel.MEDIUM

    def test_low_unchanged(self, calculator):
        """LOW level unaffected by ones_pct."""
        level = calculator._classify_level(
            score=20.0,  # Below MEDIUM threshold
            ones_pct=0.1,
        )
        assert level == SuspicionLevel.LOW

    def test_cascade_downgrade_critical_to_medium(self, calculator):
        """CRITICAL with very low ones_pct cascades to MEDIUM."""
        # Score is CRITICAL but ones_pct fails both thresholds
        level = calculator._classify_level(
            score=85.0,  # CRITICAL score
            ones_pct=0.5,  # Below both min_ones thresholds
        )
        # Should cascade: CRITICAL -> HIGH -> MEDIUM
        assert level == SuspicionLevel.MEDIUM


class TestPopularityDiscount:
    """Tests for popularity-based effect_size discount."""

    @pytest.fixture
    def calculator(self):
        """Create a metrics calculator instance."""
        return MetricsCalculator()

    def test_discount_applied_high_tens_low_ones(self, calculator):
        """Effect size discounted when tens > 45% and ones < 1.5%."""
        distribution = {
            1: 0.8,  # Low ones
            2: 0.3,
            3: 0.5,
            4: 1.0,
            5: 2.0,
            6: 5.0,
            7: 12.0,
            8: 20.0,
            9: 10.0,
            10: 48.4,  # High tens
        }
        anime_score = 9.0

        effect_size = calculator._calculate_effect_size(distribution, anime_score)

        # With discount enabled, effect should be halved
        # Calculate raw effect for comparison
        from src.core.statistics import EffectSizeCalculator, get_expected_distribution

        expected = get_expected_distribution(anime_score)
        raw_effect = EffectSizeCalculator.calculate_cohens_d(distribution, expected)

        # Effect should be approximately 0.5 * raw_effect
        assert effect_size == pytest.approx(raw_effect * 0.5, rel=0.01)

    def test_no_discount_low_tens(self, calculator):
        """No discount when tens < 45%."""
        distribution = {
            1: 0.8,
            2: 0.3,
            3: 0.5,
            4: 1.0,
            5: 3.0,
            6: 8.0,
            7: 20.0,
            8: 30.0,
            9: 15.0,
            10: 21.4,  # Below threshold
        }
        anime_score = 8.5

        effect_size = calculator._calculate_effect_size(distribution, anime_score)

        # No discount - effect should equal raw effect
        from src.core.statistics import EffectSizeCalculator, get_expected_distribution

        expected = get_expected_distribution(anime_score)
        raw_effect = EffectSizeCalculator.calculate_cohens_d(distribution, expected)

        assert effect_size == pytest.approx(raw_effect, rel=0.01)

    def test_no_discount_high_ones(self, calculator):
        """No discount when ones >= 1.5% even with high tens."""
        distribution = {
            1: 2.0,  # Above threshold
            2: 0.5,
            3: 0.8,
            4: 1.5,
            5: 3.0,
            6: 5.0,
            7: 10.0,
            8: 15.0,
            9: 12.0,
            10: 50.2,  # High tens
        }
        anime_score = 8.5

        effect_size = calculator._calculate_effect_size(distribution, anime_score)

        from src.core.statistics import EffectSizeCalculator, get_expected_distribution

        expected = get_expected_distribution(anime_score)
        raw_effect = EffectSizeCalculator.calculate_cohens_d(distribution, expected)

        assert effect_size == pytest.approx(raw_effect, rel=0.01)


class TestSpikeDamping:
    """Tests for spike ratio damping at low ones_pct."""

    @pytest.fixture
    def calculator(self):
        """Create a metrics calculator instance."""
        return MetricsCalculator()

    def test_spike_zero_below_min_ones(self, calculator):
        """Spike contribution is 0 when ones_pct < 0.5%."""
        scores = calculator._calculate_metric_scores(
            ones_zscore=5.0,
            spike_ratio=8.0,  # High spike ratio
            effect_size=0.5,
            entropy_deficit=0.1,
            bimodality=0.4,
            is_bimodal=False,
            ones_pct=0.3,  # Below min_ones_to_consider
        )

        assert scores["SPIKE"] == 0.0

    def test_spike_damped_low_ones(self, calculator):
        """Spike is damped when ones_pct < 2.0%."""
        scores_low = calculator._calculate_metric_scores(
            ones_zscore=5.0,
            spike_ratio=6.0,
            effect_size=0.5,
            entropy_deficit=0.1,
            bimodality=0.4,
            is_bimodal=False,
            ones_pct=1.0,  # 50% of min_ones_for_full_weight
        )

        scores_full = calculator._calculate_metric_scores(
            ones_zscore=5.0,
            spike_ratio=6.0,
            effect_size=0.5,
            entropy_deficit=0.1,
            bimodality=0.4,
            is_bimodal=False,
            ones_pct=3.0,  # Above min_ones_for_full_weight
        )

        # Spike at 1% ones should be approximately half of spike at 3% ones
        assert scores_low["SPIKE"] == pytest.approx(scores_full["SPIKE"] * 0.5, rel=0.1)

    def test_spike_full_weight_high_ones(self, calculator):
        """Spike at full weight when ones_pct >= 2.0%."""
        scores_2pct = calculator._calculate_metric_scores(
            ones_zscore=5.0,
            spike_ratio=6.0,
            effect_size=0.5,
            entropy_deficit=0.1,
            bimodality=0.4,
            is_bimodal=False,
            ones_pct=2.0,
        )

        scores_4pct = calculator._calculate_metric_scores(
            ones_zscore=5.0,
            spike_ratio=6.0,
            effect_size=0.5,
            entropy_deficit=0.1,
            bimodality=0.4,
            is_bimodal=False,
            ones_pct=4.0,
        )

        # Both should have the same spike score (full weight)
        assert scores_2pct["SPIKE"] == pytest.approx(scores_4pct["SPIKE"], rel=0.01)


class TestFrierenScenario:
    """Integration test for the Frieren false-positive scenario."""

    @pytest.fixture
    def calculator(self):
        """Create a metrics calculator instance."""
        return MetricsCalculator()

    def test_frieren_not_high_suspicion(self, calculator):
        """Frieren-like distribution should not be HIGH or CRITICAL.

        Frieren has: ones=0.99%, tens=55.55%, score=9.3+
        This should be classified as MEDIUM at most due to:
        1. ones_pct < min_ones_for_high (1.5%)
        2. Popularity discount on effect_size
        3. Spike damping at low ones_pct
        """
        # Simulate Frieren-like distribution
        frieren_distribution = ScoreDistribution(
            percentages={
                1: 0.99,
                2: 0.12,
                3: 0.18,
                4: 0.35,
                5: 0.80,
                6: 2.50,
                7: 7.50,
                8: 15.00,
                9: 17.01,
                10: 55.55,
            },
            vote_counts={i: int(p * 1000) for i, p in enumerate([0, 10, 1, 2, 4, 8, 25, 75, 150, 170, 556], 1)},
            total_votes=100000,
        )

        frieren_anime = AnimeData(
            mal_id=52991,
            title="Sousou no Frieren",
            score=9.3,
            rank=1,
            members=1500000,
            distribution=frieren_distribution,
        )

        metrics = calculator.calculate(frieren_anime)

        # Should NOT be HIGH or CRITICAL
        assert metrics.suspicion_level in (SuspicionLevel.LOW, SuspicionLevel.MEDIUM), \
            f"Frieren should be LOW or MEDIUM, got {metrics.suspicion_level}"

        # Bombing score should be reduced compared to original ~71
        assert metrics.bombing_score < 55, \
            f"Frieren bombing_score should be < 55, got {metrics.bombing_score}"
