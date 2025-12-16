"""Tests for ConfigView default resolution in CLI analyze command."""

from pathlib import Path

import yaml

from src.cli.commands import AnalyzeOptions, _resolve_analyze_options
from src.utils.config import Config, ConfigLoader, ConfigView


def _config(language: str = "en", platform: str = "myanimelist") -> ConfigView:
    cfg = Config()
    cfg.language = language
    cfg.default_platform = platform
    cfg.export.output_directory = "output/reports"
    return ConfigView(cfg)


def test_resolve_analyze_options_uses_config_defaults(tmp_path: Path) -> None:
    cfg = Config()
    cfg.language = "fr"
    cfg.default_platform = "kitsu"
    cfg.export.output_directory = str(tmp_path / "cfg_reports")
    cfg.export.default_format = "csv"

    view = ConfigView(cfg)

    options = _resolve_analyze_options(
        config_view=view,
        language_arg=None,
        platform_arg=None,
        output_arg=None,
        format_arg=None,
    )

    assert isinstance(options, AnalyzeOptions)
    assert options.language == "fr"
    assert options.platform == "kitsu"
    assert options.output_dir == Path(cfg.export.output_directory) / "reports"
    assert options.format_string == "csv"


def test_resolve_analyze_options_prefers_cli_over_config(tmp_path: Path) -> None:
    view = _config()

    cli_output = tmp_path / "cli_reports"

    options = _resolve_analyze_options(
        config_view=view,
        language_arg="es",
        platform_arg="anilist",
        output_arg=cli_output,
        format_arg="json",
    )

    assert options.language == "es"
    assert options.platform == "anilist"
    assert options.output_dir == cli_output
    assert options.format_string == "json"


def test_resolve_analyze_options_respects_config_file_then_cli(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    yaml.dump(
        {
            "general": {
                "language": "de",
            },
            "platforms": {
                "default": "kitsu",
            },
            "export": {
                "output_directory": str(tmp_path / "from_config"),
            },
        },
        cfg_path.open("w", encoding="utf-8"),
    )

    loaded = ConfigLoader.load(cfg_path)
    view = ConfigView(loaded)

    # No CLI overrides: config file wins
    options = _resolve_analyze_options(
        config_view=view,
        language_arg=None,
        platform_arg=None,
        output_arg=None,
        format_arg=None,
    )

    assert options.language == "de"
    assert options.platform == "kitsu"
    assert options.output_dir == Path(tmp_path / "from_config" / "reports")
    assert options.format_string == "excel,json"

    # CLI overrides take precedence over config file
    options_override = _resolve_analyze_options(
        config_view=view,
        language_arg="en",
        platform_arg="myanimelist",
        output_arg=tmp_path / "cli_output",
        format_arg="csv,json",
    )

    assert options_override.language == "en"
    assert options_override.platform == "myanimelist"
    assert options_override.output_dir == tmp_path / "cli_output"
    assert options_override.format_string == "csv,json"
