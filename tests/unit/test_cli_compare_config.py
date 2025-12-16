"""Tests for ConfigView resolution in CLI compare command."""

from src.cli.commands import CompareOptions, _resolve_compare_options
from src.utils.config import Config, ConfigView


def _config(language: str = "en", platform: str = "myanimelist") -> ConfigView:
    cfg = Config()
    cfg.language = language
    cfg.default_platform = platform
    return ConfigView(cfg)


def test_compare_resolves_config_defaults() -> None:
    view = _config(language="fr", platform="kitsu")

    options = _resolve_compare_options(
        config_view=view,
        platform_arg=None,
    )

    assert isinstance(options, CompareOptions)
    assert options.language == "fr"
    assert options.platform == "kitsu"


def test_compare_cli_platform_overrides_config() -> None:
    view = _config(language="de", platform="kitsu")

    options = _resolve_compare_options(
        config_view=view,
        platform_arg="anilist",
    )

    assert options.language == "de"
    assert options.platform == "anilist"
