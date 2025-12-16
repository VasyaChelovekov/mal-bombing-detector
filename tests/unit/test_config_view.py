"""Tests for ConfigView read-only proxy semantics."""

import pytest

from src.utils.config import Config, ConfigView, get_config, get_config_view


def test_config_view_reflects_config_defaults():
    config = get_config()
    view = get_config_view()

    assert isinstance(view, ConfigView)
    assert view.language == config.language
    assert (
        view.analysis.suspicion_thresholds.critical
        == config.analysis.suspicion_thresholds.critical
    )
    assert (
        view.analysis.metric_weights.ones_zscore
        == config.analysis.metric_weights.ones_zscore
    )
    assert view.export.output_directory == config.export.output_directory


def test_config_view_blocks_attribute_assignment():
    local_config = Config()
    view = ConfigView(local_config)

    with pytest.raises(AttributeError):
        view.language = "fr"
