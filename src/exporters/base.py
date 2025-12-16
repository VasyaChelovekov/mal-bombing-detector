"""
Base Exporter Interface

Abstract base class for all data exporters.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from src.core.analyzer import AnalysisResult
from src.utils.config import OutputConfig
from src.utils.i18n import I18n


class BaseExporter(ABC):
    """Abstract base class for data exporters."""

    def __init__(self, output_config: OutputConfig, i18n: I18n | None = None):
        """
        Initialize exporter.

        Args:
            output_config: Output configuration
            i18n: Internationalization manager
        """
        self.output_config = output_config
        self.i18n = i18n or I18n()

    @property
    @abstractmethod
    def file_extension(self) -> str:
        """Get the file extension for this exporter."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the exporter name."""
        pass

    def _get_output_path(self, base_name: str) -> Path:
        """
        Generate output file path.

        Args:
            base_name: Base name for the file

        Returns:
            Full path to output file
        """
        output_dir = Path(self.output_config.directory) / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{base_name}.{self.file_extension}"
        return output_dir / filename

    @abstractmethod
    def export(
        self, result: AnalysisResult, output_path: Path | str | None = None
    ) -> Path:
        """
        Export analysis result to file.

        Args:
            result: Analysis result to export
            output_path: Optional custom output path

        Returns:
            Path to the exported file
        """
        pass

    @abstractmethod
    def export_multiple(
        self, results: list[AnalysisResult], output_path: Path | str | None = None
    ) -> Path:
        """
        Export multiple analysis results to a single file.

        Args:
            results: List of analysis results
            output_path: Optional custom output path

        Returns:
            Path to the exported file
        """
        pass

    def _translate(self, key: str, **kwargs: Any) -> str:
        """
        Translate a key using i18n.

        Args:
            key: Translation key
            **kwargs: Interpolation values

        Returns:
            Translated string
        """
        return self.i18n.t(key, **kwargs)
