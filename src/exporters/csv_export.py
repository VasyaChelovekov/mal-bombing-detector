"""
CSV Exporter

Export analysis results to CSV format.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.models import AnalysisResult
from src.exporters.base import BaseExporter
from src.utils.config import OutputConfig
from src.utils.i18n import I18nManager


class CSVExporter(BaseExporter):
    """Export analysis results to CSV format."""
    
    def __init__(
        self,
        output_config: OutputConfig,
        i18n: I18nManager | None = None,
        delimiter: str = ",",
        include_all_metrics: bool = False
    ):
        """
        Initialize CSV exporter.
        
        Args:
            output_config: Output configuration
            i18n: Internationalization manager
            delimiter: CSV delimiter character
            include_all_metrics: Whether to include all detailed metrics
        """
        super().__init__(output_config, i18n)
        self.delimiter = delimiter
        self.include_all_metrics = include_all_metrics
    
    @property
    def file_extension(self) -> str:
        return "csv"
    
    @property
    def name(self) -> str:
        return "CSV"
    
    def export(
        self,
        result: AnalysisResult,
        output_path: Path | str | None = None
    ) -> Path:
        """Export single analysis result to CSV."""
        return self.export_multiple([result], output_path)
    
    def export_multiple(
        self,
        results: list[AnalysisResult],
        output_path: Path | str | None = None
    ) -> Path:
        """Export multiple analysis results to CSV."""
        if output_path:
            path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self._get_output_path(f"mal_bombing_data_{timestamp}")
        
        # Build rows
        rows = [self._build_row(r) for r in results]
        
        if not rows:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            return path
        
        # Get headers from first row
        headers = list(rows[0].keys())
        
        # Write to file
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers, delimiter=self.delimiter)
            writer.writeheader()
            writer.writerows(rows)
        
        return path
    
    def _build_row(self, result: AnalysisResult) -> dict[str, Any]:
        """Build a CSV row from an analysis result."""
        anime = result.anime
        metrics = result.metrics
        
        row = {
            "mal_id": anime.mal_id,
            "rank": anime.rank,
            "title": anime.title,
            "score": anime.score,
            "members": anime.members,
            "voters": anime.voters,
            "suspicion_score": round(metrics.suspicion_score, 4),
            "severity": metrics.severity.value,
            "ones_percent": round(metrics.ones_percent, 4),
            "tens_percent": round(metrics.tens_percent, 4),
        }
        
        if self.include_all_metrics:
            # Add all detailed metrics
            row.update({
                "ones_zscore": round(metrics.ones_zscore, 4),
                "spike_ratio": round(metrics.spike_ratio, 4),
                "distribution_effect_size": round(metrics.distribution_effect_size, 4),
                "entropy_deficit": round(metrics.entropy_deficit, 4),
                "bimodality_index": round(metrics.bimodality_index, 4),
                "confidence": round(metrics.confidence, 4),
                "is_reliable": metrics.is_reliable,
            })
            
            # Add component scores
            for key, value in metrics.component_scores.items():
                row[f"component_{key}"] = round(value, 4)
            
            # Add score distribution
            for score in range(1, 11):
                count = anime.score_distribution.votes.get(score, 0)
                row[f"votes_{score}"] = count
        
        return row


class TSVExporter(CSVExporter):
    """Export analysis results to TSV (tab-separated) format."""
    
    def __init__(
        self,
        output_config: OutputConfig,
        i18n: I18nManager | None = None,
        include_all_metrics: bool = False
    ):
        """Initialize TSV exporter."""
        super().__init__(output_config, i18n, delimiter="\t", include_all_metrics=include_all_metrics)
    
    @property
    def file_extension(self) -> str:
        return "tsv"
    
    @property
    def name(self) -> str:
        return "TSV"
