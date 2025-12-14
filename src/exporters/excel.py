"""
Excel Exporter

Export analysis results to Excel format with formatting and charts.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.worksheet.worksheet import Worksheet

from src.core.analyzer import AnalysisResult
from src.core.models import BombingSeverity
from src.exporters.base import BaseExporter
from src.utils.config import OutputConfig
from src.utils.i18n import I18nManager


class ExcelExporter(BaseExporter):
    """Export analysis results to Excel format."""
    
    # Color schemes for severity levels
    SEVERITY_COLORS = {
        BombingSeverity.CRITICAL: "FF0000",  # Red
        BombingSeverity.HIGH: "FF6600",      # Orange
        BombingSeverity.MODERATE: "FFCC00",  # Yellow
        BombingSeverity.LOW: "99CC00",       # Light green
        BombingSeverity.MINIMAL: "00CC00",   # Green
        BombingSeverity.NONE: "FFFFFF",      # White
    }
    
    # Header style
    HEADER_FILL = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF")
    HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    # Border style
    THIN_BORDER = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )
    
    def __init__(
        self,
        output_config: OutputConfig,
        i18n: I18nManager | None = None
    ):
        """Initialize Excel exporter."""
        super().__init__(output_config, i18n)
        
    @property
    def file_extension(self) -> str:
        return "xlsx"
    
    @property
    def name(self) -> str:
        return "Excel"
    
    def export(
        self,
        result: AnalysisResult,
        output_path: Path | str | None = None
    ) -> Path:
        """Export single analysis result to Excel."""
        return self.export_multiple([result], output_path)
    
    def export_multiple(
        self,
        results: list[AnalysisResult],
        output_path: Path | str | None = None
    ) -> Path:
        """
        Export multiple analysis results to Excel.
        
        Creates a workbook with:
        - Summary sheet with all anime
        - Individual sheets for each anime (if enabled)
        - Charts sheet
        """
        if output_path:
            path = Path(output_path)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = self._get_output_path(f"mal_bombing_analysis_{timestamp}")
        
        # Create workbook
        wb = Workbook()
        
        # Remove default sheet
        wb.remove(wb.active)
        
        # Create summary sheet
        self._create_summary_sheet(wb, results)
        
        # Create detailed metrics sheet
        self._create_metrics_sheet(wb, results)
        
        # Create score distribution sheet
        self._create_distribution_sheet(wb, results)
        
        # Create charts sheet
        self._create_charts_sheet(wb, results)
        
        # Save workbook
        path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(path)
        
        return path
    
    def _create_summary_sheet(
        self,
        wb: Workbook,
        results: list[AnalysisResult]
    ) -> Worksheet:
        """Create summary sheet with all anime."""
        ws = wb.create_sheet(self._translate("export.sheets.summary"))
        
        # Prepare data
        data = []
        for r in results:
            anime = r.anime
            metrics = r.metrics
            
            data.append({
                self._translate("export.columns.rank"): anime.rank,
                self._translate("export.columns.title"): anime.title,
                self._translate("export.columns.score"): anime.score,
                self._translate("export.columns.members"): anime.members,
                self._translate("export.columns.voters"): anime.voters,
                self._translate("export.columns.suspicion_score"): round(metrics.suspicion_score, 2),
                self._translate("export.columns.severity"): metrics.severity.value,
                self._translate("export.columns.ones_percent"): round(metrics.ones_percent, 2),
                self._translate("export.columns.tens_percent"): round(metrics.tens_percent, 2),
            })
        
        df = pd.DataFrame(data)
        
        # Write to worksheet
        self._write_dataframe(ws, df)
        
        # Apply severity colors
        severity_col = self._get_column_index(
            df, self._translate("export.columns.severity")
        )
        self._apply_severity_colors(ws, severity_col, results)
        
        # Adjust column widths
        self._auto_fit_columns(ws)
        
        return ws
    
    def _create_metrics_sheet(
        self,
        wb: Workbook,
        results: list[AnalysisResult]
    ) -> Worksheet:
        """Create detailed metrics sheet."""
        ws = wb.create_sheet(self._translate("export.sheets.metrics"))
        
        # Prepare data with all metrics
        data = []
        for r in results:
            anime = r.anime
            metrics = r.metrics
            
            row = {
                self._translate("export.columns.title"): anime.title,
                self._translate("export.columns.suspicion_score"): round(metrics.suspicion_score, 2),
                "Ones Z-Score": round(metrics.ones_zscore, 2),
                "Spike Ratio": round(metrics.spike_ratio, 2),
                "Distribution Effect Size": round(metrics.distribution_effect_size, 3),
                "Entropy Deficit": round(metrics.entropy_deficit, 3),
                "Bimodality Index": round(metrics.bimodality_index, 3),
            }
            
            # Add component scores
            for key, value in metrics.component_scores.items():
                row[f"Component: {key}"] = round(value, 3)
            
            data.append(row)
        
        df = pd.DataFrame(data)
        self._write_dataframe(ws, df)
        self._auto_fit_columns(ws)
        
        return ws
    
    def _create_distribution_sheet(
        self,
        wb: Workbook,
        results: list[AnalysisResult]
    ) -> Worksheet:
        """Create score distribution sheet."""
        ws = wb.create_sheet(self._translate("export.sheets.distribution"))
        
        # Headers
        headers = [self._translate("export.columns.title")]
        headers.extend([f"Score {i}" for i in range(1, 11)])
        headers.append("Total")
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = self.HEADER_ALIGNMENT
            cell.border = self.THIN_BORDER
        
        # Data rows
        for row_idx, r in enumerate(results, 2):
            anime = r.anime
            distribution = anime.score_distribution
            
            # Title
            ws.cell(row=row_idx, column=1, value=anime.title).border = self.THIN_BORDER
            
            # Distribution values
            total = 0
            for score in range(1, 11):
                count = distribution.votes.get(score, 0)
                total += count
                cell = ws.cell(row=row_idx, column=score + 1, value=count)
                cell.border = self.THIN_BORDER
                cell.number_format = "#,##0"
            
            # Total
            ws.cell(row=row_idx, column=12, value=total).border = self.THIN_BORDER
        
        self._auto_fit_columns(ws)
        
        return ws
    
    def _create_charts_sheet(
        self,
        wb: Workbook,
        results: list[AnalysisResult]
    ) -> Worksheet:
        """Create charts sheet."""
        ws = wb.create_sheet(self._translate("export.sheets.charts"))
        
        # Only create chart for top suspicious anime
        suspicious = [r for r in results if r.metrics.severity in [
            BombingSeverity.CRITICAL,
            BombingSeverity.HIGH,
            BombingSeverity.MODERATE
        ]][:5]
        
        if not suspicious:
            ws.cell(row=1, column=1, value="No suspicious anime found for charts")
            return ws
        
        # Prepare chart data
        ws.cell(row=1, column=1, value="Suspicion Score Comparison")
        ws.cell(row=2, column=1, value="Title")
        ws.cell(row=2, column=2, value="Score")
        
        for idx, r in enumerate(suspicious, 3):
            ws.cell(row=idx, column=1, value=r.anime.title[:30])
            ws.cell(row=idx, column=2, value=r.metrics.suspicion_score)
        
        # Create bar chart
        chart = BarChart()
        chart.type = "col"
        chart.style = 10
        chart.title = "Top Suspicious Anime"
        chart.x_axis.title = "Anime"
        chart.y_axis.title = "Suspicion Score"
        
        data = Reference(ws, min_col=2, min_row=2, max_row=2 + len(suspicious))
        categories = Reference(ws, min_col=1, min_row=3, max_row=2 + len(suspicious))
        
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(categories)
        chart.shape = 4
        chart.width = 15
        chart.height = 10
        
        ws.add_chart(chart, "D2")
        
        return ws
    
    def _write_dataframe(self, ws: Worksheet, df: pd.DataFrame) -> None:
        """Write DataFrame to worksheet with formatting."""
        # Headers
        for col, header in enumerate(df.columns, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.fill = self.HEADER_FILL
            cell.font = self.HEADER_FONT
            cell.alignment = self.HEADER_ALIGNMENT
            cell.border = self.THIN_BORDER
        
        # Data rows
        for row_idx, row in enumerate(df.itertuples(index=False), 2):
            for col_idx, value in enumerate(row, 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                cell.border = self.THIN_BORDER
                
                # Number formatting
                if isinstance(value, float):
                    cell.number_format = "#,##0.00"
                elif isinstance(value, int):
                    cell.number_format = "#,##0"
    
    def _get_column_index(self, df: pd.DataFrame, column_name: str) -> int:
        """Get 1-based column index by name."""
        try:
            return list(df.columns).index(column_name) + 1
        except ValueError:
            return -1
    
    def _apply_severity_colors(
        self,
        ws: Worksheet,
        col_idx: int,
        results: list[AnalysisResult]
    ) -> None:
        """Apply background colors based on severity."""
        if col_idx < 0:
            return
            
        for row_idx, r in enumerate(results, 2):
            cell = ws.cell(row=row_idx, column=col_idx)
            color = self.SEVERITY_COLORS.get(r.metrics.severity, "FFFFFF")
            cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            
            # Dark text for light backgrounds
            if r.metrics.severity in [BombingSeverity.MINIMAL, BombingSeverity.NONE]:
                cell.font = Font(color="000000")
            else:
                cell.font = Font(color="FFFFFF", bold=True)
    
    def _auto_fit_columns(self, ws: Worksheet) -> None:
        """Auto-fit column widths based on content."""
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except:
                    pass
            
            # Set width with some padding
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
