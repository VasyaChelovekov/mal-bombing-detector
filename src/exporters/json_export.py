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
from src.exporters.aggregation import build_export_payload
from src.exporters.base import BaseExporter
from src.utils.config import ConfigView, OutputConfig, get_config_view
from src.utils.i18n import I18nManager


class JSONExporter(BaseExporter):
    """Export analysis results to JSON format."""

    def __init__(
        self,
        output_config: OutputConfig | None = None,
        i18n: I18nManager | None = None,
        pretty: bool = True,
        config: ConfigView | None = None,
    ):
        """
        Initialize JSON exporter.

        Args:
            output_config: Optional output configuration override.
            i18n: Internationalization manager
            pretty: Whether to format JSON with indentation
            config: Optional ConfigView (falls back to global read-only view)
        """
        self.config = config or get_config_view()
        effective_output_config = output_config or self.config.export

        super().__init__(effective_output_config, i18n)
        self.pretty = pretty

    @property
    def file_extension(self) -> str:
        return "json"

    @property
    def name(self) -> str:
        return "JSON"

    def export(
        self, result: AnalysisResult, output_path: Path | str | None = None
    ) -> Path:
        """Export single analysis result to JSON."""
        return self.export_multiple([result], output_path)

    def export_multiple(
        self, results: list[AnalysisResult], output_path: Path | str | None = None
    ) -> Path:
        """Export multiple analysis results to JSON."""
        if output_path:
            path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self._get_output_path(f"mal_bombing_analysis_{timestamp}")

        # Build export data using shared helper (schema unchanged)
        export_data = build_export_payload(results, language=self.i18n.language)

        # Write to file
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            if self.pretty:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(export_data, f, ensure_ascii=False)

        return path

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
                "total_votes": anime.score_distribution.total_votes,
            },
        }

    def _serialize_metrics(self, metrics: ReviewBombingMetrics) -> dict[str, Any]:
        """Serialize bombing metrics."""
        return metrics.to_dict()
