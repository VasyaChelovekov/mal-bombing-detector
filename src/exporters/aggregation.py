"""Shared aggregation helpers for exporters.

These helpers centralize metadata, summary, results, and failures assembly
without changing any output schema. They are intentionally minimal and
side-effect free so exporters stay thin while preserving compatibility.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List

from src.core.analyzer import AnalysisResult
from src.core.models import FailureRecord, SuspicionLevel
from src._version import __version__


def aggregate_failures(results: List[AnalysisResult]) -> list[FailureRecord]:
    """Flatten failures across all results, preserving input order."""
    aggregated: list[FailureRecord] = []
    for result in results:
        aggregated.extend(result.failures)
    return aggregated


def build_metadata(
    results: List[AnalysisResult], *, language: str, version: str = __version__
) -> dict[str, Any]:
    """Build metadata with accurate counts (schema-compatible)."""
    total_requested = sum(r.summary.total_requested for r in results)
    total_analyzed = sum(r.summary.total_analyzed for r in results)
    total_failed = sum(r.summary.total_failed for r in results)
    total_skipped = sum(r.summary.total_skipped for r in results)

    return {
        "generated_at": datetime.now().isoformat(),
        "generator": "MAL Bombing Detector",
        "version": version,
        "language": language,
        "total_requested": total_requested,
        "total_analyzed": total_analyzed,
        "total_failed": total_failed,
        "total_skipped": total_skipped,
        "total_batches": len(results),
    }


def build_summary(results: List[AnalysisResult]) -> dict[str, Any]:
    """Build aggregate summary without altering schema or counts."""
    all_metrics = []
    for result in results:
        all_metrics.extend(result.metrics)

    level_counts = {level.value: 0 for level in SuspicionLevel}
    for metric in all_metrics:
        level_counts[metric.suspicion_level.value] += 1

    bombing_scores = [m.bombing_score for m in all_metrics]

    suspicious_count = (
        level_counts["medium"] + level_counts["high"] + level_counts["critical"]
    )
    highly_suspicious_count = level_counts["high"] + level_counts["critical"]

    return {
        "count_by_level": level_counts,
        "suspicious_count": suspicious_count,
        "highly_suspicious_count": highly_suspicious_count,
        "statistics": {
            "avg_bombing_score": round(sum(bombing_scores) / len(bombing_scores), 3)
            if bombing_scores
            else 0,
            "max_bombing_score": round(max(bombing_scores), 3) if bombing_scores else 0,
            "min_bombing_score": round(min(bombing_scores), 3) if bombing_scores else 0,
        },
    }


def serialize_result(result: AnalysisResult) -> dict[str, Any]:
    """Serialize a single AnalysisResult using stable schema."""
    return {
        "metrics": [metric.to_dict() for metric in result.metrics],
        "summary": result.summary.to_dict(),
        "failures": [failure.to_dict() for failure in result.failures]
        if result.failures
        else [],
    }


def build_export_payload(
    results: List[AnalysisResult], *, language: str, version: str = __version__
) -> dict[str, Any]:
    """Build the full export payload shared by JSON-like exporters."""
    export_data = {
        "metadata": build_metadata(results, language=language, version=version),
        "summary": build_summary(results),
        "results": [serialize_result(r) for r in results],
    }

    all_failures = aggregate_failures(results)
    if all_failures:
        export_data["failures"] = [failure.to_dict() for failure in all_failures]

    return export_data
