"""
JSON Exporter

Export analysis results to JSON format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.analyzer import AnalysisResult
from src.core.models import AnimeData, ReviewBombingMetrics
from src.exporters.base import BaseExporter
from src.utils.config import OutputConfig
from src.utils.i18n import I18nManager


class JSONExporter(BaseExporter):
    """Export analysis results to JSON format."""
    
    def __init__(
        self,
        output_config: OutputConfig,
        i18n: I18nManager | None = None,
        pretty: bool = True
    ):
        """
        Initialize JSON exporter.
        
        Args:
            output_config: Output configuration
            i18n: Internationalization manager
            pretty: Whether to format JSON with indentation
        """
        super().__init__(output_config, i18n)
        self.pretty = pretty
    
    @property
    def file_extension(self) -> str:
        return "json"
    
    @property
    def name(self) -> str:
        return "JSON"
    
    def export(
        self,
        result: AnalysisResult,
        output_path: Path | str | None = None
    ) -> Path:
        """Export single analysis result to JSON."""
        return self.export_multiple([result], output_path)
    
    def export_multiple(
        self,
        results: list[AnalysisResult],
        output_path: Path | str | None = None
    ) -> Path:
        """Export multiple analysis results to JSON."""
        if output_path:
            path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self._get_output_path(f"mal_bombing_analysis_{timestamp}")
        
        # Build export data
        export_data = self._build_export_data(results)
        
        # Write to file
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            if self.pretty:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(export_data, f, ensure_ascii=False)
        
        return path
    
    def _build_export_data(self, results: list[AnalysisResult]) -> dict[str, Any]:
        """Build the complete export data structure."""
        return {
            "metadata": self._build_metadata(results),
            "summary": self._build_summary(results),
            "results": [self._serialize_result(r) for r in results]
        }
    
    def _build_metadata(self, results: list[AnalysisResult]) -> dict[str, Any]:
        """Build metadata section."""
        return {
            "generated_at": datetime.now().isoformat(),
            "generator": "MAL Bombing Detector",
            "version": "1.0.0",
            "total_anime": len(results),
            "language": self.i18n.language
        }
    
    def _build_summary(self, results: list[AnalysisResult]) -> dict[str, Any]:
        """Build summary statistics."""
        from src.core.models import SuspicionLevel
        
        # Aggregate all metrics
        all_metrics = []
        for r in results:
            all_metrics.extend(r.metrics)
        
        level_counts = {level.value: 0 for level in SuspicionLevel}
        for m in all_metrics:
            level_counts[m.suspicion_level.value] += 1
        
        bombing_scores = [m.bombing_score for m in all_metrics]
        
        return {
            "level_distribution": level_counts,
            "statistics": {
                "avg_bombing_score": round(sum(bombing_scores) / len(bombing_scores), 3) if bombing_scores else 0,
                "max_bombing_score": round(max(bombing_scores), 3) if bombing_scores else 0,
                "min_bombing_score": round(min(bombing_scores), 3) if bombing_scores else 0,
                "suspicious_count": sum(1 for s in bombing_scores if s >= 35),
                "highly_suspicious_count": sum(1 for s in bombing_scores if s >= 55)
            }
        }
    
    def _serialize_result(self, result: AnalysisResult) -> dict[str, Any]:
        """Serialize a single analysis result."""
        return {
            "metrics": [self._serialize_metrics(m) for m in result.metrics],
            "summary": {
                "total_analyzed": result.summary.total_analyzed,
                "critical_count": result.summary.critical_count,
                "high_count": result.summary.high_count,
                "medium_count": result.summary.medium_count,
                "low_count": result.summary.low_count,
            }
        }
    
    def _serialize_anime(self, anime: AnimeData) -> dict[str, Any]:
        """Serialize anime data."""
        return {
            "mal_id": anime.mal_id,
            "title": anime.title,
            "english_title": anime.english_title,
            "rank": anime.rank,
            "score": anime.score,
            "members": anime.members,
            "voters": anime.voters,
            "episodes": anime.episodes,
            "anime_type": anime.anime_type,
            "status": anime.status,
            "url": anime.url,
            "score_distribution": {
                "votes": anime.score_distribution.votes,
                "total_votes": anime.score_distribution.total_votes
            }
        }
    
    def _serialize_metrics(self, metrics: ReviewBombingMetrics) -> dict[str, Any]:
        """Serialize bombing metrics."""
        return metrics.to_dict()
