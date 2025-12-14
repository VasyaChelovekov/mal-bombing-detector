"""
Configuration management for MAL Bombing Detector.

This module provides a comprehensive configuration system supporting:
- YAML configuration files
- Environment variable overrides
- Dataclass-based type-safe configuration
- Default values and validation
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# Default paths
ROOT_DIR = Path(__file__).parent.parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"
EXAMPLE_CONFIG_PATH = CONFIG_DIR / "config.example.yaml"


@dataclass
class ScrapingConfig:
    """Configuration for web scraping behavior."""
    
    request_delay: float = 2.0
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout: int = 30
    concurrent_requests: int = 1
    respect_robots_txt: bool = True


@dataclass
class CacheConfig:
    """Configuration for caching behavior."""
    
    enabled: bool = True
    directory: str = "data/cache"
    expiry_hours: int = 24
    max_entries: int = 1000
    compression: bool = False
    
    @property
    def path(self) -> Path:
        """Get cache directory as Path object."""
        return ROOT_DIR / self.directory


@dataclass
class ExpectedOnesConfig:
    """Expected ones percentage for a rating category."""
    
    mean: float
    std: float
    max_natural: float


@dataclass
class MetricWeightsConfig:
    """Weights for bombing metrics calculation."""
    
    ones_zscore: float = 0.35
    spike_anomaly: float = 0.20
    distribution_effect: float = 0.20
    bimodality: float = 0.15
    entropy_deficit: float = 0.10
    
    def validate(self) -> bool:
        """Validate that weights sum to 1.0."""
        total = (self.ones_zscore + self.spike_anomaly + 
                 self.distribution_effect + self.bimodality + 
                 self.entropy_deficit)
        return abs(total - 1.0) < 0.01
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            'ones_zscore': self.ones_zscore,
            'spike_anomaly': self.spike_anomaly,
            'distribution_effect': self.distribution_effect,
            'bimodality': self.bimodality,
            'entropy_deficit': self.entropy_deficit,
        }


@dataclass
class SuspicionThresholdsConfig:
    """Thresholds for suspicion level classification."""
    
    critical: int = 75
    high: int = 55
    medium: int = 35
    low: int = 0


@dataclass
class StatisticalThresholdsConfig:
    """Statistical thresholds for anomaly detection."""
    
    # Z-score thresholds
    ones_zscore_extreme: float = 3.0
    ones_zscore_significant: float = 2.0
    ones_zscore_notable: float = 1.65
    
    # Spike ratio thresholds
    spike_ratio_extreme: float = 4.0
    spike_ratio_elevated: float = 2.5
    spike_ratio_normal_max: float = 2.0
    
    # Effect size thresholds
    effect_size_large: float = 1.0
    effect_size_medium: float = 0.5
    effect_size_small: float = 0.2
    
    # Bimodality thresholds
    bimodality_confirmed: float = 0.4
    bimodality_possible: float = 0.3
    
    # Entropy deficit thresholds
    entropy_deficit_warning: float = 0.15
    entropy_deficit_normal_max: float = 0.10


@dataclass
class FormatAdjustmentsConfig:
    """Adjustment factors for different anime formats."""
    
    movie: float = 0.90
    ova: float = 0.90
    special: float = 0.90
    sequel: float = 0.85
    default: float = 1.0


@dataclass
class AnalysisConfig:
    """Configuration for analysis parameters."""
    
    min_votes_threshold: int = 1000
    
    expected_ones_by_rating: Dict[str, ExpectedOnesConfig] = field(default_factory=dict)
    metric_weights: MetricWeightsConfig = field(default_factory=MetricWeightsConfig)
    suspicion_thresholds: SuspicionThresholdsConfig = field(default_factory=SuspicionThresholdsConfig)
    statistical_thresholds: StatisticalThresholdsConfig = field(default_factory=StatisticalThresholdsConfig)
    format_adjustments: FormatAdjustmentsConfig = field(default_factory=FormatAdjustmentsConfig)
    
    age_old_threshold_years: int = 15
    age_old_factor: float = 0.95
    age_default_factor: float = 1.0
    
    def __post_init__(self):
        """Initialize default expected ones if not provided."""
        if not self.expected_ones_by_rating:
            self.expected_ones_by_rating = {
                'elite': ExpectedOnesConfig(mean=0.4, std=0.25, max_natural=1.2),
                'excellent': ExpectedOnesConfig(mean=0.7, std=0.35, max_natural=1.8),
                'great': ExpectedOnesConfig(mean=1.2, std=0.5, max_natural=2.8),
                'good': ExpectedOnesConfig(mean=2.0, std=0.8, max_natural=4.5),
                'average': ExpectedOnesConfig(mean=3.5, std=1.2, max_natural=7.0),
            }


@dataclass
class ChartConfig:
    """Configuration for chart generation."""
    
    dpi: int = 150
    figure_size: List[int] = field(default_factory=lambda: [12, 8])
    style: str = "seaborn-v0_8-whitegrid"
    color_palette: str = "husl"


@dataclass
class LevelColorsConfig:
    """Color scheme for suspicion levels."""
    
    critical: str = "#d62728"
    high: str = "#ff7f0e"
    medium: str = "#ffbb33"
    low: str = "#2ca02c"


@dataclass
class VisualizationConfig:
    """Configuration for visualization."""
    
    enabled: bool = True
    output_directory: str = "output/charts"
    charts: ChartConfig = field(default_factory=ChartConfig)
    level_colors: LevelColorsConfig = field(default_factory=LevelColorsConfig)
    
    @property
    def output_path(self) -> Path:
        """Get output directory as Path object."""
        return ROOT_DIR / self.output_directory


@dataclass
class ExportFormatsConfig:
    """Configuration for export formats."""
    
    excel_enabled: bool = True
    excel_include_charts: bool = True
    excel_include_severity_sheet: bool = True
    
    csv_enabled: bool = True
    csv_delimiter: str = ","
    csv_encoding: str = "utf-8"
    
    json_enabled: bool = False
    json_pretty_print: bool = True
    json_indent: int = 2
    
    html_enabled: bool = False
    html_template: str = "default"
    
    markdown_enabled: bool = False


@dataclass
class ExportConfig:
    """Configuration for export."""
    
    output_directory: str = "output/reports"
    formats: ExportFormatsConfig = field(default_factory=ExportFormatsConfig)
    
    @property
    def output_path(self) -> Path:
        """Get output directory as Path object."""
        return ROOT_DIR / self.output_directory


@dataclass
class LoggingConfig:
    """Configuration for logging."""
    
    directory: str = "output/logs"
    filename_pattern: str = "analysis_{date}.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    @property
    def path(self) -> Path:
        """Get log directory as Path object."""
        return ROOT_DIR / self.directory


@dataclass
class CLIConfig:
    """Configuration for CLI."""
    
    show_progress_bar: bool = True
    colored_output: bool = True
    default_limit: int = 50


@dataclass
class APIConfig:
    """Configuration for REST API."""
    
    enabled: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    rate_limit: int = 100


@dataclass
class PlatformConfig:
    """Configuration for a specific platform."""
    
    name: str
    base_url: str = ""
    api_url: str = ""
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


@dataclass
class Config:
    """Main configuration class."""
    
    language: str = "en"
    log_level: str = "INFO"
    timezone: str = "UTC"
    
    default_platform: str = "myanimelist"
    platforms: Dict[str, PlatformConfig] = field(default_factory=dict)
    
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    cli: CLIConfig = field(default_factory=CLIConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    def __post_init__(self):
        """Initialize default platforms if not provided."""
        if not self.platforms:
            self.platforms = {
                'myanimelist': PlatformConfig(
                    name='myanimelist',
                    base_url='https://myanimelist.net',
                    api_url='https://api.myanimelist.net/v2',
                ),
                'anilist': PlatformConfig(
                    name='anilist',
                    api_url='https://graphql.anilist.co',
                ),
                'kitsu': PlatformConfig(
                    name='kitsu',
                    api_url='https://kitsu.io/api/edge',
                ),
            }


class ConfigLoader:
    """
    Configuration loader with support for YAML files and environment variables.
    
    Priority (highest to lowest):
    1. Environment variables (MAL_ANALYZER_*)
    2. User config file (config.yaml)
    3. Default values
    
    Example:
        >>> config = ConfigLoader.load()
        >>> config = ConfigLoader.load("custom_config.yaml")
    """
    
    ENV_PREFIX = "MAL_ANALYZER_"
    
    @classmethod
    def load(cls, config_path: Optional[str | Path] = None) -> Config:
        """
        Load configuration from file and environment.
        
        Args:
            config_path: Optional path to configuration file.
                        If None, tries default locations.
        
        Returns:
            Config: Loaded configuration object.
        """
        # Try to find config file
        if config_path:
            path = Path(config_path)
        elif DEFAULT_CONFIG_PATH.exists():
            path = DEFAULT_CONFIG_PATH
        elif EXAMPLE_CONFIG_PATH.exists():
            path = EXAMPLE_CONFIG_PATH
        else:
            # Use defaults
            return cls._apply_env_overrides(Config())
        
        # Load YAML
        data = cls._load_yaml(path)
        
        # Build config
        config = cls._build_config(data)
        
        # Apply environment overrides
        config = cls._apply_env_overrides(config)
        
        return config
    
    @classmethod
    def _load_yaml(cls, path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
    
    @classmethod
    def _build_config(cls, data: Dict[str, Any]) -> Config:
        """Build Config object from dictionary data."""
        general = data.get('general', {})
        
        config = Config(
            language=general.get('language', 'en'),
            log_level=general.get('log_level', 'INFO'),
            timezone=general.get('timezone', 'UTC'),
            default_platform=data.get('platforms', {}).get('default', 'myanimelist'),
        )
        
        # Load scraping config
        scraping_data = data.get('scraping', {})
        config.scraping = ScrapingConfig(
            request_delay=scraping_data.get('request_delay', 2.0),
            max_retries=scraping_data.get('max_retries', 3),
            retry_delay=scraping_data.get('retry_delay', 5.0),
            timeout=scraping_data.get('timeout', 30),
            concurrent_requests=scraping_data.get('concurrent_requests', 1),
            respect_robots_txt=scraping_data.get('respect_robots_txt', True),
        )
        
        # Load cache config
        cache_data = data.get('cache', {})
        config.cache = CacheConfig(
            enabled=cache_data.get('enabled', True),
            directory=cache_data.get('directory', 'data/cache'),
            expiry_hours=cache_data.get('expiry_hours', 24),
            max_entries=cache_data.get('max_entries', 1000),
            compression=cache_data.get('compression', False),
        )
        
        # Load analysis config
        analysis_data = data.get('analysis', {})
        cls._load_analysis_config(config, analysis_data)
        
        # Load visualization config
        viz_data = data.get('visualization', {})
        cls._load_visualization_config(config, viz_data)
        
        # Load export config
        export_data = data.get('export', {})
        cls._load_export_config(config, export_data)
        
        # Load CLI config
        cli_data = data.get('cli', {})
        config.cli = CLIConfig(
            show_progress_bar=cli_data.get('show_progress_bar', True),
            colored_output=cli_data.get('colored_output', True),
            default_limit=cli_data.get('default_limit', 50),
        )
        
        # Load API config
        api_data = data.get('api', {})
        config.api = APIConfig(
            enabled=api_data.get('enabled', False),
            host=api_data.get('host', '0.0.0.0'),
            port=api_data.get('port', 8000),
            cors_origins=api_data.get('cors_origins', ['*']),
            rate_limit=api_data.get('rate_limit', 100),
        )
        
        return config
    
    @classmethod
    def _load_analysis_config(cls, config: Config, data: Dict[str, Any]) -> None:
        """Load analysis configuration section."""
        config.analysis.min_votes_threshold = data.get('min_votes_threshold', 1000)
        
        # Load expected ones by rating
        expected_data = data.get('expected_ones_by_rating', {})
        for category, values in expected_data.items():
            if isinstance(values, dict):
                config.analysis.expected_ones_by_rating[category] = ExpectedOnesConfig(
                    mean=values.get('mean', 1.0),
                    std=values.get('std', 0.5),
                    max_natural=values.get('max_natural', 2.0),
                )
        
        # Load metric weights
        weights_data = data.get('metric_weights', {})
        config.analysis.metric_weights = MetricWeightsConfig(
            ones_zscore=weights_data.get('ones_zscore', 0.35),
            spike_anomaly=weights_data.get('spike_anomaly', 0.20),
            distribution_effect=weights_data.get('distribution_effect', 0.20),
            bimodality=weights_data.get('bimodality', 0.15),
            entropy_deficit=weights_data.get('entropy_deficit', 0.10),
        )
        
        # Load suspicion thresholds
        suspicion_data = data.get('suspicion_thresholds', {})
        config.analysis.suspicion_thresholds = SuspicionThresholdsConfig(
            critical=suspicion_data.get('critical', 75),
            high=suspicion_data.get('high', 55),
            medium=suspicion_data.get('medium', 35),
            low=suspicion_data.get('low', 0),
        )
        
        # Load statistical thresholds
        stat_data = data.get('statistical_thresholds', {})
        ones_z = stat_data.get('ones_zscore', {})
        spike = stat_data.get('spike_ratio', {})
        effect = stat_data.get('effect_size', {})
        bimod = stat_data.get('bimodality', {})
        entropy = stat_data.get('entropy_deficit', {})
        
        config.analysis.statistical_thresholds = StatisticalThresholdsConfig(
            ones_zscore_extreme=ones_z.get('extreme', 3.0),
            ones_zscore_significant=ones_z.get('significant', 2.0),
            ones_zscore_notable=ones_z.get('notable', 1.65),
            spike_ratio_extreme=spike.get('extreme', 4.0),
            spike_ratio_elevated=spike.get('elevated', 2.5),
            spike_ratio_normal_max=spike.get('normal_max', 2.0),
            effect_size_large=effect.get('large', 1.0),
            effect_size_medium=effect.get('medium', 0.5),
            effect_size_small=effect.get('small', 0.2),
            bimodality_confirmed=bimod.get('confirmed', 0.4),
            bimodality_possible=bimod.get('possible', 0.3),
            entropy_deficit_warning=entropy.get('warning', 0.15),
            entropy_deficit_normal_max=entropy.get('normal_max', 0.10),
        )
        
        # Load format adjustments
        format_data = data.get('format_adjustments', {})
        config.analysis.format_adjustments = FormatAdjustmentsConfig(
            movie=format_data.get('movie', 0.90),
            ova=format_data.get('ova', 0.90),
            special=format_data.get('special', 0.90),
            sequel=format_data.get('sequel', 0.85),
            default=format_data.get('default', 1.0),
        )
        
        # Load age adjustments
        age_data = data.get('age_adjustments', {})
        config.analysis.age_old_threshold_years = age_data.get('old_threshold_years', 15)
        config.analysis.age_old_factor = age_data.get('old_factor', 0.95)
        config.analysis.age_default_factor = age_data.get('default', 1.0)
    
    @classmethod
    def _load_visualization_config(cls, config: Config, data: Dict[str, Any]) -> None:
        """Load visualization configuration section."""
        config.visualization.enabled = data.get('enabled', True)
        config.visualization.output_directory = data.get('output_directory', 'output/charts')
        
        charts_data = data.get('charts', {})
        config.visualization.charts = ChartConfig(
            dpi=charts_data.get('dpi', 150),
            figure_size=charts_data.get('figure_size', [12, 8]),
            style=charts_data.get('style', 'seaborn-v0_8-whitegrid'),
            color_palette=charts_data.get('color_palette', 'husl'),
        )
        
        colors_data = data.get('level_colors', {})
        config.visualization.level_colors = LevelColorsConfig(
            critical=colors_data.get('critical', '#d62728'),
            high=colors_data.get('high', '#ff7f0e'),
            medium=colors_data.get('medium', '#ffbb33'),
            low=colors_data.get('low', '#2ca02c'),
        )
    
    @classmethod
    def _load_export_config(cls, config: Config, data: Dict[str, Any]) -> None:
        """Load export configuration section."""
        config.export.output_directory = data.get('output_directory', 'output/reports')
        
        formats_data = data.get('formats', {})
        excel = formats_data.get('excel', {})
        csv = formats_data.get('csv', {})
        json = formats_data.get('json', {})
        html = formats_data.get('html', {})
        md = formats_data.get('markdown', {})
        
        config.export.formats = ExportFormatsConfig(
            excel_enabled=excel.get('enabled', True),
            excel_include_charts=excel.get('include_charts', True),
            excel_include_severity_sheet=excel.get('include_severity_sheet', True),
            csv_enabled=csv.get('enabled', True),
            csv_delimiter=csv.get('delimiter', ','),
            csv_encoding=csv.get('encoding', 'utf-8'),
            json_enabled=json.get('enabled', False),
            json_pretty_print=json.get('pretty_print', True),
            json_indent=json.get('indent', 2),
            html_enabled=html.get('enabled', False),
            html_template=html.get('template', 'default'),
            markdown_enabled=md.get('enabled', False),
        )
    
    @classmethod
    def _apply_env_overrides(cls, config: Config) -> Config:
        """Apply environment variable overrides."""
        # Language
        if lang := os.environ.get(f"{cls.ENV_PREFIX}LANGUAGE"):
            config.language = lang
        
        # Log level
        if level := os.environ.get(f"{cls.ENV_PREFIX}LOG_LEVEL"):
            config.log_level = level
        
        # Scraping delay
        if delay := os.environ.get(f"{cls.ENV_PREFIX}REQUEST_DELAY"):
            config.scraping.request_delay = float(delay)
        
        # Cache
        if cache := os.environ.get(f"{cls.ENV_PREFIX}CACHE_ENABLED"):
            config.cache.enabled = cache.lower() in ('true', '1', 'yes')
        
        if expiry := os.environ.get(f"{cls.ENV_PREFIX}CACHE_EXPIRY_HOURS"):
            config.cache.expiry_hours = int(expiry)
        
        # API
        if port := os.environ.get(f"{cls.ENV_PREFIX}API_PORT"):
            config.api.port = int(port)
        
        if host := os.environ.get(f"{cls.ENV_PREFIX}API_HOST"):
            config.api.host = host
        
        return config


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: The global configuration object.
    """
    global _config
    if _config is None:
        _config = ConfigLoader.load()
    return _config


def reload_config(config_path: Optional[str | Path] = None) -> Config:
    """
    Reload configuration from file.
    
    Args:
        config_path: Optional path to configuration file.
    
    Returns:
        Config: The reloaded configuration object.
    """
    global _config
    _config = ConfigLoader.load(config_path)
    return _config
