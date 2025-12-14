"""
JSON Exporter

Export analysis results to JSON format.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.models import AnalysisResult, AnimeData, BombingMetrics
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
            "version": "2.0.0",
            "total_anime": len(results),
            "language": self.i18n.get_language()
        }
    
    def _build_summary(self, results: list[AnalysisResult]) -> dict[str, Any]:
        """Build summary statistics."""
        from src.core.models import BombingSeverity
        
        severity_counts = {}
        for severity in BombingSeverity:
            count = sum(1 for r in results if r.metrics.severity == severity)
            severity_counts[severity.value] = count
        
        suspicion_scores = [r.metrics.suspicion_score for r in results]
        
        return {
            "severity_distribution": severity_counts,
            "statistics": {
                "avg_suspicion_score": round(sum(suspicion_scores) / len(suspicion_scores), 3) if suspicion_scores else 0,
                "max_suspicion_score": round(max(suspicion_scores), 3) if suspicion_scores else 0,
                "min_suspicion_score": round(min(suspicion_scores), 3) if suspicion_scores else 0,
                "suspicious_count": sum(1 for s in suspicion_scores if s >= 0.5),
                "highly_suspicious_count": sum(1 for s in suspicion_scores if s >= 0.7)
            }
        }
    
    def _serialize_result(self, result: AnalysisResult) -> dict[str, Any]:
        """Serialize a single analysis result."""
        return {
            "anime": self._serialize_anime(result.anime),
            "metrics": self._serialize_metrics(result.metrics),
            "analysis_timestamp": result.timestamp.isoformat() if result.timestamp else None
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
    
    def _serialize_metrics(self, metrics: BombingMetrics) -> dict[str, Any]:
        """Serialize bombing metrics."""
        return {
            "suspicion_score": round(metrics.suspicion_score, 4),
            "severity": metrics.severity.value,
            "severity_reason": metrics.severity_reason,
            "primary_metrics": {
                "ones_percent": round(metrics.ones_percent, 4),
                "tens_percent": round(metrics.tens_percent, 4),
                "ones_zscore": round(metrics.ones_zscore, 4),
                "spike_ratio": round(metrics.spike_ratio, 4),
                "distribution_effect_size": round(metrics.distribution_effect_size, 4),
                "entropy_deficit": round(metrics.entropy_deficit, 4),
                "bimodality_index": round(metrics.bimodality_index, 4)
            },
            "component_scores": {
                k: round(v, 4) for k, v in metrics.component_scores.items()
            },
            "flags": metrics.flags,
            "confidence": round(metrics.confidence, 4),
            "is_reliable": metrics.is_reliable
        }
