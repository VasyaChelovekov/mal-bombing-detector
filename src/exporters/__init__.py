"""
Exporters Package

Provides various export formats for analysis results.
"""

from src.exporters.base import BaseExporter
from src.exporters.csv_export import CSVExporter, TSVExporter
from src.exporters.excel import ExcelExporter
from src.exporters.html_export import HTMLExporter
from src.exporters.json_export import JSONExporter

__all__ = [
    "BaseExporter",
    "CSVExporter",
    "TSVExporter",
    "ExcelExporter",
    "HTMLExporter",
    "JSONExporter",
    "get_exporter",
]


def get_exporter(format_type: str, output_config, i18n=None, **kwargs) -> BaseExporter:
    """
    Factory function to get an exporter by format type.

    Args:
        format_type: Export format (excel, json, csv, tsv, html)
        output_config: Output configuration
        i18n: Internationalization manager
        **kwargs: Additional exporter-specific arguments

    Returns:
        Appropriate exporter instance

    Raises:
        ValueError: If format type is not supported
    """
    exporters = {
        "excel": ExcelExporter,
        "xlsx": ExcelExporter,
        "json": JSONExporter,
        "csv": CSVExporter,
        "tsv": TSVExporter,
        "html": HTMLExporter,
    }

    format_lower = format_type.lower()

    if format_lower not in exporters:
        supported = ", ".join(sorted(set(exporters.keys())))
        raise ValueError(
            f"Unsupported export format: {format_type}. Supported: {supported}"
        )

    exporter_class = exporters[format_lower]
    return exporter_class(output_config, i18n, **kwargs)
