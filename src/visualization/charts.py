"""
Chart Generator

Generate various charts for analysis visualization.
"""

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from src.core.analyzer import AnalysisResult
from src.core.models import BombingSeverity
from src.utils.config import OutputConfig
from src.utils.i18n import I18nManager
from src.visualization.themes import Theme, get_theme


class ChartGenerator:
    """Generate visualization charts for analysis results."""
    
    def __init__(
        self,
        output_config: OutputConfig,
        i18n: I18nManager | None = None,
        theme: Theme | str = "default"
    ):
        """
        Initialize chart generator.
        
        Args:
            output_config: Output configuration
            i18n: Internationalization manager
            theme: Theme instance or theme name
        """
        self.output_config = output_config
        self.i18n = i18n or I18nManager()
        
        if isinstance(theme, str):
            self.theme = get_theme(theme)
        else:
            self.theme = theme
        
        self.palette = self.theme.palette
        
        # Apply theme
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply theme to matplotlib."""
        plt.rcParams.update(self.theme.to_matplotlib_style())
    
    def _get_output_path(self, name: str) -> Path:
        """Get output path for a chart."""
        output_dir = Path(self.output_config.directory) / "charts"
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / f"{name}.png"
    
    def _translate(self, key: str, **kwargs: Any) -> str:
        """Translate a key."""
        return self.i18n.t(key, **kwargs)
    
    def generate_all(
        self,
        results: list[AnalysisResult],
        prefix: str = ""
    ) -> list[Path]:
        """
        Generate all available charts.
        
        Args:
            results: Analysis results
            prefix: Prefix for output filenames
            
        Returns:
            List of generated chart paths
        """
        charts = []
        
        charts.append(self.severity_distribution(results, prefix))
        charts.append(self.suspicion_scores(results, prefix))
        charts.append(self.score_distribution_comparison(results, prefix))
        charts.append(self.metrics_correlation(results, prefix))
        charts.append(self.ones_vs_score_scatter(results, prefix))
        
        # Individual distribution charts for suspicious anime
        suspicious = [r for r in results if r.metrics.suspicion_score >= 0.5][:5]
        for r in suspicious:
            path = self.single_distribution(r, prefix)
            charts.append(path)
        
        return charts
    
    def severity_distribution(
        self,
        results: list[AnalysisResult],
        prefix: str = ""
    ) -> Path:
        """
        Generate severity distribution pie chart.
        
        Args:
            results: Analysis results
            prefix: Prefix for output filename
            
        Returns:
            Path to generated chart
        """
        # Count severities
        counts = {s: 0 for s in BombingSeverity}
        for r in results:
            counts[r.metrics.severity] += 1
        
        # Filter out zero counts
        labels = []
        sizes = []
        colors = []
        
        for severity in BombingSeverity:
            if counts[severity] > 0:
                labels.append(severity.value)
                sizes.append(counts[severity])
                colors.append(self.palette.get_severity_color(severity.value))
        
        # Create chart
        fig, ax = plt.subplots(figsize=(10, 8))
        
        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*sum(sizes))})',
            startangle=90,
            explode=[0.05 if label in ['critical', 'high'] else 0 for label in labels]
        )
        
        ax.set_title(
            self._translate("charts.severity_distribution.title"),
            fontsize=14,
            fontweight='bold'
        )
        
        plt.tight_layout()
        
        # Save
        filename = f"{prefix}severity_distribution" if prefix else "severity_distribution"
        path = self._get_output_path(filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
    
    def suspicion_scores(
        self,
        results: list[AnalysisResult],
        prefix: str = ""
    ) -> Path:
        """
        Generate suspicion scores bar chart.
        
        Args:
            results: Analysis results
            prefix: Prefix for output filename
            
        Returns:
            Path to generated chart
        """
        # Sort by suspicion score
        sorted_results = sorted(
            results,
            key=lambda r: r.metrics.suspicion_score,
            reverse=True
        )[:20]  # Top 20
        
        titles = [r.anime.title[:30] for r in sorted_results]
        scores = [r.metrics.suspicion_score for r in sorted_results]
        colors = [
            self.palette.get_severity_color(r.metrics.severity.value)
            for r in sorted_results
        ]
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 10))
        
        bars = ax.barh(range(len(titles)), scores, color=colors)
        ax.set_yticks(range(len(titles)))
        ax.set_yticklabels(titles)
        ax.invert_yaxis()
        
        ax.set_xlabel(self._translate("charts.suspicion_scores.xlabel"))
        ax.set_title(
            self._translate("charts.suspicion_scores.title"),
            fontsize=14,
            fontweight='bold'
        )
        
        # Add value labels
        for bar, score in zip(bars, scores):
            ax.text(
                bar.get_width() + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f'{score:.2f}',
                va='center',
                fontsize=9
            )
        
        # Add threshold lines
        ax.axvline(x=0.7, color=self.palette.critical, linestyle='--', alpha=0.7, label='Critical')
        ax.axvline(x=0.5, color=self.palette.moderate, linestyle='--', alpha=0.7, label='Moderate')
        
        ax.legend(loc='lower right')
        
        plt.tight_layout()
        
        # Save
        filename = f"{prefix}suspicion_scores" if prefix else "suspicion_scores"
        path = self._get_output_path(filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
    
    def score_distribution_comparison(
        self,
        results: list[AnalysisResult],
        prefix: str = ""
    ) -> Path:
        """
        Generate score distribution comparison chart.
        
        Args:
            results: Analysis results
            prefix: Prefix for output filename
            
        Returns:
            Path to generated chart
        """
        # Get top suspicious and top clean
        sorted_results = sorted(results, key=lambda r: r.metrics.suspicion_score, reverse=True)
        
        suspicious = sorted_results[:3]
        clean = sorted_results[-3:]
        
        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        for idx, (row_results, row_title) in enumerate([
            (suspicious, "Most Suspicious"),
            (clean, "Least Suspicious")
        ]):
            for col, r in enumerate(row_results):
                ax = axes[idx, col]
                
                distribution = r.anime.score_distribution
                votes = [distribution.votes.get(i, 0) for i in range(1, 11)]
                percentages = [v / sum(votes) * 100 if sum(votes) > 0 else 0 for v in votes]
                
                colors = self.palette.get_score_colors()
                ax.bar(range(1, 11), percentages, color=colors)
                
                ax.set_xlabel("Score")
                ax.set_ylabel("Percentage")
                ax.set_title(
                    f"{r.anime.title[:25]}\n(Suspicion: {r.metrics.suspicion_score:.2f})",
                    fontsize=10
                )
                ax.set_xticks(range(1, 11))
        
        fig.suptitle(
            self._translate("charts.distribution_comparison.title"),
            fontsize=14,
            fontweight='bold'
        )
        
        plt.tight_layout()
        
        # Save
        filename = f"{prefix}distribution_comparison" if prefix else "distribution_comparison"
        path = self._get_output_path(filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
    
    def single_distribution(
        self,
        result: AnalysisResult,
        prefix: str = ""
    ) -> Path:
        """
        Generate single anime score distribution chart.
        
        Args:
            result: Single analysis result
            prefix: Prefix for output filename
            
        Returns:
            Path to generated chart
        """
        distribution = result.anime.score_distribution
        votes = [distribution.votes.get(i, 0) for i in range(1, 11)]
        percentages = [v / sum(votes) * 100 if sum(votes) > 0 else 0 for v in votes]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        colors = self.palette.get_score_colors()
        bars = ax.bar(range(1, 11), percentages, color=colors)
        
        # Highlight anomalies
        ones_pct = percentages[0]
        if ones_pct > 5:  # Highlight if 1s > 5%
            bars[0].set_edgecolor(self.palette.critical)
            bars[0].set_linewidth(3)
        
        ax.set_xlabel("Score")
        ax.set_ylabel("Percentage of Votes")
        ax.set_title(
            f"{result.anime.title}\n"
            f"Suspicion Score: {result.metrics.suspicion_score:.2f} | "
            f"Severity: {result.metrics.severity.value}",
            fontsize=12,
            fontweight='bold'
        )
        ax.set_xticks(range(1, 11))
        
        # Add annotations
        for i, (bar, pct) in enumerate(zip(bars, percentages)):
            if pct > 2:  # Only label significant bars
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f'{pct:.1f}%',
                    ha='center',
                    fontsize=9
                )
        
        plt.tight_layout()
        
        # Save
        anime_id = result.anime.mal_id
        filename = f"{prefix}distribution_{anime_id}" if prefix else f"distribution_{anime_id}"
        path = self._get_output_path(filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
    
    def metrics_correlation(
        self,
        results: list[AnalysisResult],
        prefix: str = ""
    ) -> Path:
        """
        Generate metrics correlation heatmap.
        
        Args:
            results: Analysis results
            prefix: Prefix for output filename
            
        Returns:
            Path to generated chart
        """
        import pandas as pd
        
        # Build metrics dataframe
        data = []
        for r in results:
            m = r.metrics
            data.append({
                'suspicion_score': m.suspicion_score,
                'ones_zscore': m.ones_zscore,
                'spike_ratio': m.spike_ratio,
                'effect_size': m.distribution_effect_size,
                'entropy_deficit': m.entropy_deficit,
                'bimodality': m.bimodality_index,
                'ones_percent': m.ones_percent,
            })
        
        df = pd.DataFrame(data)
        
        # Calculate correlation matrix
        corr = df.corr()
        
        # Create heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(
            corr,
            annot=True,
            fmt='.2f',
            cmap='RdYlBu_r',
            center=0,
            ax=ax,
            square=True
        )
        
        ax.set_title(
            self._translate("charts.metrics_correlation.title"),
            fontsize=14,
            fontweight='bold'
        )
        
        plt.tight_layout()
        
        # Save
        filename = f"{prefix}metrics_correlation" if prefix else "metrics_correlation"
        path = self._get_output_path(filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
    
    def ones_vs_score_scatter(
        self,
        results: list[AnalysisResult],
        prefix: str = ""
    ) -> Path:
        """
        Generate scatter plot of 1-votes percentage vs MAL score.
        
        Args:
            results: Analysis results
            prefix: Prefix for output filename
            
        Returns:
            Path to generated chart
        """
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Group by severity
        for severity in BombingSeverity:
            severity_results = [r for r in results if r.metrics.severity == severity]
            
            if severity_results:
                x = [r.anime.score for r in severity_results]
                y = [r.metrics.ones_percent for r in severity_results]
                
                ax.scatter(
                    x, y,
                    c=self.palette.get_severity_color(severity.value),
                    label=severity.value,
                    alpha=0.7,
                    s=80
                )
        
        ax.set_xlabel("MAL Score")
        ax.set_ylabel("1-Votes Percentage")
        ax.set_title(
            self._translate("charts.ones_vs_score.title"),
            fontsize=14,
            fontweight='bold'
        )
        ax.legend()
        
        plt.tight_layout()
        
        # Save
        filename = f"{prefix}ones_vs_score" if prefix else "ones_vs_score"
        path = self._get_output_path(filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
    
    def suspicion_heatmap(
        self,
        results: list[AnalysisResult],
        prefix: str = ""
    ) -> Path:
        """
        Generate suspicion score heatmap by rank.
        
        Args:
            results: Analysis results
            prefix: Prefix for output filename
            
        Returns:
            Path to generated chart
        """
        
        # Sort by rank
        sorted_results = sorted(results, key=lambda r: r.anime.rank or 999)[:50]
        
        # Create data grid
        titles = [r.anime.title[:20] for r in sorted_results]
        scores = [r.metrics.suspicion_score for r in sorted_results]
        
        # Reshape for heatmap (5 columns)
        n_cols = 5
        n_rows = (len(titles) + n_cols - 1) // n_cols
        
        data = np.zeros((n_rows, n_cols))
        labels = [['' for _ in range(n_cols)] for _ in range(n_rows)]
        
        for i, (title, score) in enumerate(zip(titles, scores)):
            row = i // n_cols
            col = i % n_cols
            data[row, col] = score
            labels[row][col] = title
        
        fig, ax = plt.subplots(figsize=(15, 10))
        
        sns.heatmap(
            data,
            annot=labels,
            fmt='',
            cmap='RdYlGn_r',
            ax=ax,
            cbar_kws={'label': 'Suspicion Score'}
        )
        
        ax.set_title(
            self._translate("charts.suspicion_heatmap.title"),
            fontsize=14,
            fontweight='bold'
        )
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        
        plt.tight_layout()
        
        # Save
        filename = f"{prefix}suspicion_heatmap" if prefix else "suspicion_heatmap"
        path = self._get_output_path(filename)
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return path
