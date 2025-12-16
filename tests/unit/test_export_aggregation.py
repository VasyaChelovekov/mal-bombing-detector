"""Tests for exporter aggregation helpers (schema compatibility)."""

from src.core.analyzer import AnalysisResult
from src.core.models import (
    AnalysisSummary,
    FailureRecord,
    FailureStage,
    ReviewBombingMetrics,
    SuspicionLevel,
)
from src.exporters.aggregation import (
    aggregate_failures,
    build_export_payload,
    build_metadata,
    build_summary,
    serialize_result,
)


def _metrics(
    score: float, level: SuspicionLevel, mal_id: int = 1
) -> ReviewBombingMetrics:
    return ReviewBombingMetrics(
        mal_id=mal_id,
        title=f"title-{mal_id}",
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


def _summary(
    total_requested: int, total_analyzed: int, total_failed: int, total_skipped: int
) -> AnalysisSummary:
    return AnalysisSummary(
        total_requested=total_requested,
        total_analyzed=total_analyzed,
        total_failed=total_failed,
        total_skipped=total_skipped,
        score_mean=0,
        score_median=0,
        score_std=0,
        score_min=0,
        score_max=0,
        ones_mean=0,
        ones_median=0,
        ones_max=0,
        critical_count=0,
        high_count=0,
        medium_count=0,
        low_count=0,
    )


def test_metadata_and_summary_match_counts():
    metrics = [
        _metrics(80, SuspicionLevel.CRITICAL, 1),
        _metrics(40, SuspicionLevel.MEDIUM, 2),
    ]
    summary = _summary(
        total_requested=3, total_analyzed=2, total_failed=1, total_skipped=0
    )
    failures = [
        FailureRecord.from_message(
            1, FailureStage.FETCH, "NetworkError", "failed fetch"
        ),
        FailureRecord.from_message(
            2, FailureStage.PARSE, "NoDistribution", "no distribution"
        ),
    ]
    result = AnalysisResult(metrics=metrics, summary=summary, failures=failures)

    meta = build_metadata([result], language="en", version="1.1.0")
    assert meta["total_requested"] == 3
    assert meta["total_analyzed"] == 2
    assert meta["total_failed"] == 1
    assert meta["total_skipped"] == 0
    assert meta["total_batches"] == 1
    assert meta["language"] == "en"
    assert meta["version"] == "1.1.0"

    summary_payload = build_summary([result])
    assert summary_payload["count_by_level"] == {
        "critical": 1,
        "high": 0,
        "medium": 1,
        "low": 0,
    }
    assert summary_payload["suspicious_count"] == 2
    assert summary_payload["highly_suspicious_count"] == 1
    assert summary_payload["statistics"]["avg_bombing_score"] == 60.0
    assert summary_payload["statistics"]["max_bombing_score"] == 80.0
    assert summary_payload["statistics"]["min_bombing_score"] == 40.0


def test_failures_order_and_payload_shape():
    metrics = [_metrics(75, SuspicionLevel.CRITICAL, 5)]
    summary = _summary(
        total_requested=1, total_analyzed=1, total_failed=1, total_skipped=0
    )
    failures = [
        FailureRecord.from_message(5, FailureStage.FETCH, "NetworkError", "first"),
        FailureRecord.from_message(5, FailureStage.ANALYZE, "ValueError", "second"),
    ]
    result = AnalysisResult(metrics=metrics, summary=summary, failures=failures)

    aggregated = aggregate_failures([result])
    assert [f.message for f in aggregated] == ["first", "second"]  # preserves order

    payload = build_export_payload([result], language="en", version="1.1.0")
    assert "metadata" in payload and "summary" in payload and "results" in payload
    assert payload["metadata"]["total_failed"] == 1
    assert payload["summary"]["count_by_level"]["critical"] == 1
    assert payload["results"][0]["failures"][0]["stage"] == "fetch"
    assert payload["failures"][1]["stage"] == "analyze"

    serialized = serialize_result(result)
    assert serialized["summary"]["total_analyzed"] == 1
    assert len(serialized["metrics"]) == 1
