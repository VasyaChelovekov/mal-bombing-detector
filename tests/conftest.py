"""
Test configuration and fixtures.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_score_distribution():
    """Sample score distribution for testing."""
    return {
        1: 500,
        2: 200,
        3: 300,
        4: 400,
        5: 800,
        6: 1500,
        7: 3000,
        8: 5000,
        9: 4000,
        10: 2000
    }


@pytest.fixture
def bombed_score_distribution():
    """Score distribution with bombing pattern."""
    return {
        1: 5000,  # High spike at 1
        2: 200,
        3: 150,
        4: 200,
        5: 300,
        6: 500,
        7: 1000,
        8: 2000,
        9: 3000,
        10: 4000
    }


@pytest.fixture
def normal_score_distribution():
    """Normal score distribution (no bombing)."""
    return {
        1: 50,
        2: 80,
        3: 150,
        4: 300,
        5: 600,
        6: 1200,
        7: 2500,
        8: 4500,
        9: 3500,
        10: 1500
    }


@pytest.fixture
def test_output_dir(tmp_path):
    """Temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "analysis": {
            "metrics": {
                "weights": {
                    "ones_zscore": 0.25,
                    "spike_ratio": 0.20,
                    "distribution_effect_size": 0.20,
                    "entropy_deficit": 0.15,
                    "bimodality": 0.10,
                    "contextual": 0.10
                },
                "thresholds": {
                    "severity": {
                        "critical": 0.80,
                        "high": 0.65,
                        "moderate": 0.50,
                        "low": 0.35,
                        "minimal": 0.20
                    }
                }
            }
        }
    }
