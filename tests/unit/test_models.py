"""
Unit tests for models module.
"""

import pytest
from datetime import datetime

from src.core.models import (
    AnimeData,
    ScoreDistribution,
    ReviewBombingMetrics,
    SeverityLevel,
    SuspicionLevel,
)


class TestScoreDistribution:
    """Tests for ScoreDistribution class."""
    
    def test_total_votes(self, sample_score_distribution):
        """Test total votes calculation."""
        dist = ScoreDistribution(
            vote_counts=sample_score_distribution,
            total_votes=sum(sample_score_distribution.values())
        )
        expected_total = sum(sample_score_distribution.values())
        
        assert dist.total_votes == expected_total
    
    def test_empty_distribution(self):
        """Test empty distribution."""
        dist = ScoreDistribution(vote_counts={}, total_votes=0)
        
        assert dist.total_votes == 0
    
    def test_percentages(self, sample_score_distribution):
        """Test percentages calculation."""
        total = sum(sample_score_distribution.values())
        percentages = {k: (v / total * 100) for k, v in sample_score_distribution.items()}
        
        dist = ScoreDistribution(
            vote_counts=sample_score_distribution,
            percentages=percentages,
            total_votes=total
        )
        
        # All percentages should sum to approximately 100
        assert sum(dist.percentages.values()) == pytest.approx(100.0, rel=0.01)


class TestAnimeData:
    """Tests for AnimeData class."""
    
    def test_creation(self, sample_score_distribution):
        """Test anime data creation."""
        total = sum(sample_score_distribution.values())
        dist = ScoreDistribution(
            vote_counts=sample_score_distribution,
            total_votes=total
        )
        
        anime = AnimeData(
            mal_id=12345,
            title="Test Anime",
            score=8.5,
            members=100000,
            url="https://myanimelist.net/anime/12345",
            rank=10,
            distribution=dist
        )
        
        assert anime.mal_id == 12345
        assert anime.title == "Test Anime"
        assert anime.score == 8.5
        assert anime.rank == 10
    
    def test_url_field(self):
        """Test URL field."""
        anime = AnimeData(
            mal_id=12345,
            title="Test",
            score=8.0,
            url="https://myanimelist.net/anime/12345"
        )
        
        assert "12345" in anime.url
    
    def test_optional_fields_defaults(self):
        """Test optional fields have defaults."""
        anime = AnimeData(
            mal_id=1,
            title="Test",
            score=7.0,
            url=""
        )
        
        assert anime.rank == 0
        assert anime.members == 0
        assert anime.distribution is None


class TestReviewBombingMetrics:
    """Tests for ReviewBombingMetrics class."""
    
    def test_creation(self):
        """Test metrics creation."""
        metrics = ReviewBombingMetrics(
            mal_id=12345,
            title="Test Anime",
            ones_zscore=3.5,
            distribution_effect_size=0.8,
            spike_ratio=4.2,
            entropy_deficit=0.3,
            bimodality_coefficient=0.65,
            ones_percentage=15.5,
            tens_percentage=25.0,
            bombing_score=75.0,
            suspicion_level=SuspicionLevel.HIGH
        )
        
        assert metrics.mal_id == 12345
        assert metrics.bombing_score == 75.0
        assert metrics.suspicion_level == SuspicionLevel.HIGH
        assert metrics.ones_percentage == 15.5
    
    def test_default_values(self):
        """Test default values for optional fields."""
        metrics = ReviewBombingMetrics(
            mal_id=1,
            title="Test",
            ones_zscore=2.0,
            distribution_effect_size=0.5,
            spike_ratio=2.0,
            entropy_deficit=0.2,
            bimodality_coefficient=0.4,
            ones_percentage=10.0,
            tens_percentage=20.0,
            bombing_score=50.0
        )
        
        assert metrics.adjusted_score == 0.0
        assert metrics.bombing_rank == 0
        assert metrics.metric_breakdown == {}
        assert metrics.anomaly_flags == []


class TestSuspicionLevel:
    """Tests for SuspicionLevel enum."""
    
    def test_all_levels(self):
        """Test all suspicion level values."""
        expected = ['critical', 'high', 'medium', 'low']
        actual = [s.value for s in SuspicionLevel]
        
        assert set(actual) == set(expected)


class TestSeverityLevel:
    """Tests for SeverityLevel enum."""
    
    def test_severity_values(self):
        """Test all severity enum values."""
        expected = ['extreme', 'severe', 'moderate', 'light', 'none']
        actual = [s.value for s in SeverityLevel]
        
        assert set(actual) == set(expected)
