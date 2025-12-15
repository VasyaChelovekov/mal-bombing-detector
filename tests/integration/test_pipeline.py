"""
Integration tests for the analysis pipeline.

These tests verify that all components work together correctly.
"""

import pytest

from src.core.analyzer import BombingAnalyzer, AnalysisResult
from src.core.metrics import MetricsCalculator
from src.core.models import AnimeData, ScoreDistribution, SuspicionLevel


class TestAnalysisPipeline:
    """Integration tests for the full analysis pipeline."""
    
    @pytest.fixture
    def sample_anime_list(self):
        """Create a list of sample anime with distributions."""
        anime_list = []
        
        # Normal anime (no bombing)
        normal_votes = {1: 50, 2: 80, 3: 150, 4: 300, 5: 600, 
                       6: 1200, 7: 2500, 8: 4500, 9: 3500, 10: 1500}
        total = sum(normal_votes.values())
        normal_pct = {k: (v / total * 100) for k, v in normal_votes.items()}
        
        anime_list.append(AnimeData(
            mal_id=1,
            title="Normal Anime",
            score=8.5,
            url="https://myanimelist.net/anime/1",
            rank=1,
            members=100000,
            distribution=ScoreDistribution(
                vote_counts=normal_votes,
                percentages=normal_pct,
                total_votes=total
            )
        ))
        
        # Suspected bombed anime (high 1s)
        bombed_votes = {1: 5000, 2: 200, 3: 150, 4: 200, 5: 300,
                       6: 500, 7: 1000, 8: 2000, 9: 3000, 10: 4000}
        total_b = sum(bombed_votes.values())
        bombed_pct = {k: (v / total_b * 100) for k, v in bombed_votes.items()}
        
        anime_list.append(AnimeData(
            mal_id=2,
            title="Suspected Bombed Anime",
            score=7.8,
            url="https://myanimelist.net/anime/2",
            rank=50,
            members=50000,
            distribution=ScoreDistribution(
                vote_counts=bombed_votes,
                percentages=bombed_pct,
                total_votes=total_b
            )
        ))
        
        # Polarized anime (high 1s and 10s)
        polar_votes = {1: 3000, 2: 100, 3: 100, 4: 100, 5: 200,
                      6: 300, 7: 500, 8: 1000, 9: 2000, 10: 5000}
        total_p = sum(polar_votes.values())
        polar_pct = {k: (v / total_p * 100) for k, v in polar_votes.items()}
        
        anime_list.append(AnimeData(
            mal_id=3,
            title="Polarized Anime",
            score=8.0,
            url="https://myanimelist.net/anime/3",
            rank=25,
            members=75000,
            distribution=ScoreDistribution(
                vote_counts=polar_votes,
                percentages=polar_pct,
                total_votes=total_p
            )
        ))
        
        return anime_list
    
    def test_full_analysis_pipeline(self, sample_anime_list):
        """Test the complete analysis pipeline from data to results."""
        # Create analyzer
        analyzer = BombingAnalyzer()
        
        # Run batch analysis
        results = analyzer.analyze_batch(sample_anime_list)
        
        # Verify results structure
        assert isinstance(results, AnalysisResult)
        assert len(results.metrics) == 3
        assert results.summary is not None
        assert results.summary.total_analyzed == 3
    
    def test_metrics_ranking(self, sample_anime_list):
        """Test that metrics are ranked correctly by bombing score."""
        analyzer = BombingAnalyzer()
        results = analyzer.analyze_batch(sample_anime_list)
        
        # Check ranking exists
        for m in results.metrics:
            assert m.bombing_rank > 0
        
        # Check ranking is unique
        ranks = [m.bombing_rank for m in results.metrics]
        assert len(ranks) == len(set(ranks))
    
    def test_bombed_detection(self, sample_anime_list):
        """Test that bombed anime is detected with higher suspicion."""
        analyzer = BombingAnalyzer()
        results = analyzer.analyze_batch(sample_anime_list)
        
        # Find metrics by title
        metrics_by_title = {m.title: m for m in results.metrics}
        
        normal = metrics_by_title["Normal Anime"]
        bombed = metrics_by_title["Suspected Bombed Anime"]
        
        # Bombed should have higher bombing score
        assert bombed.bombing_score > normal.bombing_score
        
        # Bombed should have higher ones percentage
        assert bombed.ones_percentage > normal.ones_percentage
    
    def test_suspicion_levels_assigned(self, sample_anime_list):
        """Test that all anime get suspicion levels assigned."""
        analyzer = BombingAnalyzer()
        results = analyzer.analyze_batch(sample_anime_list)
        
        for m in results.metrics:
            assert m.suspicion_level is not None
            assert isinstance(m.suspicion_level, SuspicionLevel)
    
    def test_summary_statistics(self, sample_anime_list):
        """Test summary statistics are calculated correctly."""
        analyzer = BombingAnalyzer()
        results = analyzer.analyze_batch(sample_anime_list)
        
        summary = results.summary
        
        # Basic checks
        assert summary.total_analyzed == 3
        assert summary.score_mean >= 0
        assert summary.score_std >= 0
        
        # Level counts should sum to total
        level_total = (summary.critical_count + summary.high_count + 
                      summary.medium_count + summary.low_count)
        assert level_total == summary.total_analyzed


class TestMetricsCalculatorIntegration:
    """Integration tests for MetricsCalculator."""
    
    def test_calculate_with_real_distribution(self):
        """Test metrics calculation with realistic distribution."""
        calculator = MetricsCalculator()
        
        # Real-ish distribution data
        votes = {1: 1500, 2: 300, 3: 400, 4: 500, 5: 800, 
                6: 1500, 7: 3000, 8: 5000, 9: 4000, 10: 3000}
        total = sum(votes.values())
        pct = {k: (v / total * 100) for k, v in votes.items()}
        
        anime = AnimeData(
            mal_id=12345,
            title="Test Anime",
            score=8.2,
            url="",
            distribution=ScoreDistribution(
                vote_counts=votes,
                percentages=pct,
                total_votes=total
            )
        )
        
        metrics = calculator.calculate(anime)
        
        # Verify all fields populated
        assert metrics.mal_id == 12345
        assert metrics.title == "Test Anime"
        assert 0 <= metrics.bombing_score <= 100
        assert metrics.ones_percentage > 0
        assert metrics.tens_percentage > 0
        assert metrics.suspicion_level is not None
    
    def test_rank_by_bombing(self):
        """Test ranking functionality."""
        calculator = MetricsCalculator()
        
        # Create multiple anime
        anime_list = []
        for i, ones_count in enumerate([100, 1000, 5000]):
            votes = {1: ones_count, 2: 100, 3: 200, 4: 300, 5: 500,
                    6: 1000, 7: 2000, 8: 3000, 9: 2500, 10: 2000}
            total = sum(votes.values())
            pct = {k: (v / total * 100) for k, v in votes.items()}
            
            anime_list.append(AnimeData(
                mal_id=i + 1,
                title=f"Anime {i + 1}",
                score=8.0 - i * 0.2,
                url="",
                distribution=ScoreDistribution(
                    vote_counts=votes,
                    percentages=pct,
                    total_votes=total
                )
            ))
        
        # Calculate metrics for all
        metrics_list = [calculator.calculate(a) for a in anime_list]
        
        # Rank them
        ranked = calculator.rank_by_bombing(metrics_list)
        
        # The one with most 1s should rank first (most suspicious)
        assert ranked[0].mal_id == 3  # The one with 5000 ones
        assert ranked[-1].mal_id == 1  # The one with 100 ones
