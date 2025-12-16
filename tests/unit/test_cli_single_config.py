"""Tests for ConfigView resolution in CLI single command."""

from pathlib import Path

import yaml

from src.cli.commands import SingleOptions, _resolve_single_options
from src.utils.config import Config, ConfigLoader, ConfigView


def _config(language: str = "en", platform: str = "myanimelist") -> ConfigView:
    cfg = Config()
    cfg.language = language
    cfg.default_platform = platform
    return ConfigView(cfg)


def test_single_resolves_config_defaults(tmp_path: Path) -> None:
    cfg = Config()
    cfg.language = "fr"
    cfg.default_platform = "kitsu"

    view = ConfigView(cfg)

    options = _resolve_single_options(
        config_view=view,
        platform_arg=None,
    )

    assert isinstance(options, SingleOptions)
    assert options.language == "fr"
    assert options.platform == "kitsu"


def test_single_cli_platform_overrides_config(tmp_path: Path) -> None:
    view = _config(language="de", platform="kitsu")

    options = _resolve_single_options(
        config_view=view,
        platform_arg="anilist",
    )

    assert options.language == "de"
    assert options.platform == "anilist"


def test_single_respects_config_file_then_cli_override(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yaml"
    yaml.dump(
        {
            "general": {"language": "ja"},
            "platforms": {"default": "kitsu"},
        },
        cfg_path.open("w", encoding="utf-8"),
    )

    loaded = ConfigLoader.load(cfg_path)
    view = ConfigView(loaded)

    # Config file values applied when CLI does not override
    options = _resolve_single_options(
        config_view=view,
        platform_arg=None,
    )

    assert options.language == "ja"
    assert options.platform == "kitsu"

    # CLI platform wins over config file
    override = _resolve_single_options(
        config_view=view,
        platform_arg="anilist",
    )

    assert override.language == "ja"
    assert override.platform == "anilist"
