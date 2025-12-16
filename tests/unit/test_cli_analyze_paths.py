"""CLI analyze output path resolution tests using Typer runner."""

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

from src.cli import commands
from src.cli.commands import app
from src.core.analyzer import AnalysisResult
from src.core.models import AnalysisSummary

runner = CliRunner()


class _DummyPlatform:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakeExporter:
    file_extension = "json"

    def __init__(self, output_config: Any, i18n: Any = None, **_: Any) -> None:
        self.output_config = output_config
        self.i18n = i18n
        self.received_paths: list[Path] = []

    def export(
        self, result: AnalysisResult, output_path: Path | str | None = None
    ) -> Path:
        return self.export_multiple([result], output_path)

    def export_multiple(
        self, results: list[AnalysisResult], output_path: Path | str | None = None
    ) -> Path:
        path = Path(output_path)
        self.received_paths.append(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}", encoding="utf-8")
        return path


async def _dummy_run_analysis(
    platform: Any, limit: int, no_cache: bool
) -> AnalysisResult:  # noqa: ARG001
    summary = AnalysisSummary(
        total_requested=limit,
        total_analyzed=0,
        total_failed=0,
        total_skipped=0,
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
    return AnalysisResult(metrics=[], summary=summary, failures=[])


def _write_config(tmp_path: Path, out_dir: Path) -> Path:
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        """
export:
  output_directory: """
        + str(out_dir).replace("\\", "/")
        + "\n",
        encoding="utf-8",
    )
    return cfg_path


def _monkeypatch_cli(monkeypatch, out_dir: Path, holder: dict[str, Any]):
    monkeypatch.setattr(commands, "get_platform", lambda name: _DummyPlatform())
    monkeypatch.setattr(commands, "run_analysis", _dummy_run_analysis)
    monkeypatch.setattr(
        commands,
        "get_exporter",
        lambda fmt, cfg, i18n=None, **_: holder.setdefault(
            "exporter", _FakeExporter(cfg, i18n)
        ),
    )


def test_analyze_uses_config_output_base_once(tmp_path, monkeypatch):
    base_out = tmp_path / "out"
    cfg_path = _write_config(tmp_path, base_out)

    holder: dict[str, Any] = {}
    _monkeypatch_cli(monkeypatch, base_out, holder)

    result = runner.invoke(
        app,
        [
            "analyze",
            "--config",
            str(cfg_path),
            "--limit",
            "1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.stdout
    exporter = holder["exporter"]
    assert len(exporter.received_paths) == 1

    generated = sorted((base_out / "reports").glob("top_1_analysis_*.json"))
    assert len(generated) == 1
    assert exporter.received_paths[0].parent == base_out / "reports"


def test_analyze_cli_output_overrides_config(tmp_path, monkeypatch):
    base_out = tmp_path / "out"
    cfg_path = _write_config(tmp_path, base_out)
    cli_out = tmp_path / "cli_out"

    holder: dict[str, Any] = {}
    _monkeypatch_cli(monkeypatch, base_out, holder)

    result = runner.invoke(
        app,
        [
            "analyze",
            "--config",
            str(cfg_path),
            "--output",
            str(cli_out),
            "--limit",
            "1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.stdout
    exporter = holder["exporter"]
    assert len(exporter.received_paths) == 1

    generated = sorted(cli_out.glob("top_1_analysis_*.json"))
    assert len(generated) == 1
    assert exporter.received_paths[0].parent == cli_out


def test_analyze_respects_reports_suffix_without_duplication(tmp_path, monkeypatch):
    base_out = tmp_path / "out" / "reports"
    cfg_path = _write_config(tmp_path, base_out)

    holder: dict[str, Any] = {}
    _monkeypatch_cli(monkeypatch, base_out, holder)

    result = runner.invoke(
        app,
        [
            "analyze",
            "--config",
            str(cfg_path),
            "--limit",
            "1",
            "--format",
            "json",
        ],
    )

    assert result.exit_code == 0, result.stdout
    exporter = holder["exporter"]
    assert len(exporter.received_paths) == 1

    generated = sorted(base_out.glob("top_1_analysis_*.json"))
    assert len(generated) == 1
    assert exporter.received_paths[0].parent == base_out
