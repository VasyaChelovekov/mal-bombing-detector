"""
Visualization Themes

Color schemes and styling for charts.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ColorPalette:
    """Color palette for charts."""
    
    primary: str = "#667eea"
    secondary: str = "#764ba2"
    success: str = "#28a745"
    warning: str = "#ffc107"
    danger: str = "#dc3545"
    info: str = "#17a2b8"
    
    # Severity colors
    critical: str = "#dc3545"
    high: str = "#fd7e14"
    moderate: str = "#ffc107"
    low: str = "#28a745"
    minimal: str = "#20c997"
    none: str = "#6c757d"
    
    # Score distribution colors (1-10)
    score_1: str = "#dc3545"
    score_2: str = "#e74c3c"
    score_3: str = "#fd7e14"
    score_4: str = "#f39c12"
    score_5: str = "#ffc107"
    score_6: str = "#d4ac0d"
    score_7: str = "#9acd32"
    score_8: str = "#28a745"
    score_9: str = "#20c997"
    score_10: str = "#17a2b8"
    
    # Background colors
    background: str = "#ffffff"
    grid: str = "#e0e0e0"
    text: str = "#333333"
    text_secondary: str = "#666666"
    
    def get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        colors = {
            "critical": self.critical,
            "high": self.high,
            "moderate": self.moderate,
            "low": self.low,
            "minimal": self.minimal,
            "none": self.none,
        }
        return colors.get(severity.lower(), self.none)
    
    def get_score_colors(self) -> list[str]:
        """Get list of colors for scores 1-10."""
        return [
            self.score_1, self.score_2, self.score_3, self.score_4, self.score_5,
            self.score_6, self.score_7, self.score_8, self.score_9, self.score_10
        ]
    
    def get_gradient(self, start: str, end: str, steps: int = 10) -> list[str]:
        """Generate color gradient between two colors."""
        # Simple linear interpolation
        def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
        
        start_rgb = hex_to_rgb(start)
        end_rgb = hex_to_rgb(end)
        
        gradient = []
        for i in range(steps):
            ratio = i / (steps - 1) if steps > 1 else 0
            rgb = tuple(
                int(start_rgb[j] + (end_rgb[j] - start_rgb[j]) * ratio)
                for j in range(3)
            )
            gradient.append(rgb_to_hex(rgb))
        
        return gradient


@dataclass
class Theme:
    """Chart theme configuration."""
    
    name: str
    palette: ColorPalette
    
    # Font settings
    font_family: str = "sans-serif"
    font_size_title: int = 14
    font_size_label: int = 11
    font_size_tick: int = 10
    
    # Figure settings
    figure_dpi: int = 100
    figure_facecolor: str = "#ffffff"
    
    # Axes settings
    axes_facecolor: str = "#ffffff"
    axes_edgecolor: str = "#cccccc"
    axes_linewidth: float = 1.0
    
    # Grid settings
    grid_enabled: bool = True
    grid_alpha: float = 0.3
    grid_linestyle: str = "--"
    
    # Legend settings
    legend_facecolor: str = "#ffffff"
    legend_edgecolor: str = "#cccccc"
    legend_framealpha: float = 0.9
    
    def to_matplotlib_style(self) -> dict[str, Any]:
        """Convert theme to matplotlib rcParams style dict."""
        return {
            "font.family": self.font_family,
            "font.size": self.font_size_label,
            
            "figure.dpi": self.figure_dpi,
            "figure.facecolor": self.figure_facecolor,
            
            "axes.facecolor": self.axes_facecolor,
            "axes.edgecolor": self.axes_edgecolor,
            "axes.linewidth": self.axes_linewidth,
            "axes.titlesize": self.font_size_title,
            "axes.labelsize": self.font_size_label,
            
            "axes.grid": self.grid_enabled,
            "grid.alpha": self.grid_alpha,
            "grid.linestyle": self.grid_linestyle,
            "grid.color": self.palette.grid,
            
            "xtick.labelsize": self.font_size_tick,
            "ytick.labelsize": self.font_size_tick,
            
            "legend.facecolor": self.legend_facecolor,
            "legend.edgecolor": self.legend_edgecolor,
            "legend.framealpha": self.legend_framealpha,
            
            "text.color": self.palette.text,
            "axes.labelcolor": self.palette.text,
            "xtick.color": self.palette.text,
            "ytick.color": self.palette.text,
        }


# Predefined themes
DEFAULT_THEME = Theme(
    name="default",
    palette=ColorPalette()
)

DARK_THEME = Theme(
    name="dark",
    palette=ColorPalette(
        background="#1e1e1e",
        grid="#404040",
        text="#ffffff",
        text_secondary="#aaaaaa"
    ),
    figure_facecolor="#1e1e1e",
    axes_facecolor="#2d2d2d",
    axes_edgecolor="#404040",
    legend_facecolor="#2d2d2d",
    legend_edgecolor="#404040"
)

SEABORN_THEME = Theme(
    name="seaborn",
    palette=ColorPalette(
        primary="#4c72b0",
        secondary="#55a868",
        danger="#c44e52",
        warning="#ccb974"
    ),
    axes_facecolor="#eaeaf2",
    grid_enabled=True,
    grid_alpha=0.5
)

MINIMAL_THEME = Theme(
    name="minimal",
    palette=ColorPalette(
        primary="#333333",
        secondary="#666666"
    ),
    axes_edgecolor="#ffffff",
    grid_enabled=False
)


def get_theme(name: str) -> Theme:
    """
    Get a theme by name.
    
    Args:
        name: Theme name (default, dark, seaborn, minimal)
        
    Returns:
        Theme instance
    """
    themes = {
        "default": DEFAULT_THEME,
        "dark": DARK_THEME,
        "seaborn": SEABORN_THEME,
        "minimal": MINIMAL_THEME,
    }
    
    return themes.get(name.lower(), DEFAULT_THEME)
