"""Tests for reporting and classification consistency."""

import pytest

from src.core.analyzer import BombingAnalyzer
from src.core.metrics import MetricsCalculator
from src.core.models import ReviewBombingMetrics, SuspicionLevel


def _dummy_metrics(score: float, level: SuspicionLevel) -> ReviewBombingMetrics:
    """Helper to build minimal ReviewBombingMetrics with given score/level."""
    return ReviewBombingMetrics(
        mal_id=1,
        title="dummy",
        ones_zscore=0.0,
        distribution_effect_size=0.0,
        spike_ratio=0.0,
        entropy_deficit=0.0,
        bimodality_coefficient=0.0,
        ones_percentage=0.0,
        tens_percentage=0.0,
        bombing_score=score,
        adjusted_score=score,
        suspicion_level=level,
        bombing_rank=0,
    )


class TestSuspicionClassification:
    @pytest.fixture
    def calculator(self):
        return MetricsCalculator()

    @pytest.mark.parametrize(
        "score,ones_pct,expected",
        [
            # LOW level - no ones_pct requirement
            (0.0, 0.0, SuspicionLevel.LOW),
            (24.99, 0.0, SuspicionLevel.LOW),
            # MEDIUM level - no ones_pct requirement
            (35.0, 0.0, SuspicionLevel.MEDIUM),
            (54.99, 0.0, SuspicionLevel.MEDIUM),
            # HIGH level - requires ones_pct >= 1.5%
            (55.0, 1.5, SuspicionLevel.HIGH),
            (74.99, 2.0, SuspicionLevel.HIGH),
            # CRITICAL level - requires ones_pct >= 2.0%
            (75.0, 2.0, SuspicionLevel.CRITICAL),
            (100.0, 3.0, SuspicionLevel.CRITICAL),
            # HIGH/CRITICAL without sufficient ones_pct -> downgrade
            (55.0, 0.5, SuspicionLevel.MEDIUM),  # HIGH -> MEDIUM
            (75.0, 1.0, SuspicionLevel.MEDIUM),  # CRITICAL -> HIGH -> MEDIUM
            (80.0, 1.8, SuspicionLevel.HIGH),    # CRITICAL -> HIGH (ones < 2.0)
        ],
    )
    def test_classification_is_score_based(self, calculator, score, ones_pct, expected):
        assert calculator._classify_level(score, ones_pct=ones_pct) == expected


class TestSummaryReconciliation:
    def test_counts_reconcile_with_levels(self):
        analyzer = BombingAnalyzer()
        metrics = [
            _dummy_metrics(80, SuspicionLevel.CRITICAL),
            _dummy_metrics(70, SuspicionLevel.HIGH),
            _dummy_metrics(40, SuspicionLevel.MEDIUM),
            _dummy_metrics(20, SuspicionLevel.LOW),
        ]

        summary = analyzer._generate_summary(
            metrics,
            total_requested=4,
            total_failed=1,
            total_skipped=0,
        )

        assert summary.total_requested == 4
        assert summary.total_failed == 1
        assert summary.total_analyzed == 4

        assert summary.count_by_level == {
            "critical": 1,
            "high": 1,
            "medium": 1,
            "low": 1,
        }
        assert summary.suspicious_count == 3  # medium + high + critical
        assert summary.highly_suspicious_count == 2  # high + critical
