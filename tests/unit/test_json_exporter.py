"""Tests for JSON exporter ConfigView adoption and payload integrity."""

import json
from pathlib import Path

from src._version import __version__
from src.core.analyzer import AnalysisResult
from src.core.models import AnalysisSummary, ReviewBombingMetrics, SuspicionLevel
from src.exporters.json_export import JSONExporter
from src.utils.config import ExportConfig, get_config_view
from src.utils.i18n import I18nManager


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


def test_json_exporter_defaults_to_config_view(tmp_path: Path) -> None:
    metrics = [_metrics(55.0, SuspicionLevel.HIGH, 101)]
    summary = _summary(1, 1, 0, 0)
    result = AnalysisResult(metrics=metrics, summary=summary, failures=[])

    exporter = JSONExporter(i18n=I18nManager(language="en"), pretty=False)

    config_view = get_config_view()
    assert exporter.output_config is config_view.export

    output_file = tmp_path / "analysis.json"
    path = exporter.export_multiple([result], output_file)

    assert path == output_file
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["metadata"]["language"] == "en"
    assert data["metadata"]["version"] == __version__
    assert data["results"][0]["metrics"][0]["mal_id"] == 101


def test_json_exporter_respects_explicit_output_config(tmp_path: Path) -> None:
    metrics = [_metrics(42.0, SuspicionLevel.MEDIUM, 202)]
    summary = _summary(1, 1, 0, 0)
    result = AnalysisResult(metrics=metrics, summary=summary, failures=[])

    export_dir = tmp_path / "custom_output"
    export_config = ExportConfig(output_directory=str(export_dir))

    exporter = JSONExporter(export_config, I18nManager(language="en"), pretty=False)

    path = exporter.export_multiple([result])

    assert path.parent == export_dir / "reports"
    assert path.is_file()

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["results"][0]["metrics"][0]["mal_id"] == 202
    assert data["metadata"]["language"] == "en"
