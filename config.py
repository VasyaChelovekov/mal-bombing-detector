"""
MAL Review Bombing Analyzer Project Configuration
"""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"
CHARTS_DIR = OUTPUT_DIR / "charts"
REPORTS_DIR = OUTPUT_DIR / "reports"

# Create directories
for directory in [DATA_DIR, CACHE_DIR, OUTPUT_DIR, CHARTS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# MAL Configuration
MAL_BASE_URL = "https://myanimelist.net"
MAL_TOP_ANIME_URL = f"{MAL_BASE_URL}/topanime.php"
MAL_ANIME_STATS_URL = f"{MAL_BASE_URL}/anime/{{anime_id}}/{{anime_slug}}/stats"

# Scraping settings
REQUEST_DELAY = 2.0  # Delay between requests (seconds)
MAX_RETRIES = 3
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Analysis settings
TOP_ANIME_COUNT = 100  # Number of anime to analyze
MIN_VOTES_THRESHOLD = 1000  # Minimum votes for analysis

# Metric weights for Composite Suspicion Score
METRIC_WEIGHTS = {
    'extreme_rating_ratio': 0.15,      # ERR
    'low_score_anomaly': 0.35,         # LSA - main metric for review bombing
    'distribution_deviation': 0.20,    # DDS
    'rating_distribution_mismatch': 0.30  # RDM
}

# Threshold values for classification
# Calibrated for MAL top anime:
# - Low: minor deviation, possibly natural
# - Medium: noticeable deviation, possible small bombing
# - High: clear signs of coordinated bombing
# - Critical: massive review bombing
SUSPICION_THRESHOLDS = {
    'low': 25,       # < 25: low level
    'medium': 45,    # 25-45: medium level  
    'high': 65,      # 45-65: high level
    'critical': 80   # > 65: critical (80+ = extreme)
}

# Expected score distribution for high-rated anime (8.5+)
# Used as baseline for comparison
EXPECTED_DISTRIBUTION_HIGH_RATED = {
    1: 1.0,   # Expected percentage
    2: 0.5,
    3: 0.8,
    4: 1.2,
    5: 2.5,
    6: 5.0,
    7: 12.0,
    8: 25.0,
    9: 30.0,
    10: 22.0
}

# Visualization
CHART_STYLE = 'seaborn-v0_8-whitegrid'
CHART_DPI = 150
CHART_FIGSIZE = (12, 8)
COLOR_PALETTE = 'coolwarm'

# Excel formatting
EXCEL_HEADER_COLOR = '#1F4E79'
EXCEL_HEADER_FONT_COLOR = '#FFFFFF'
EXCEL_ALTERNATING_ROW_COLOR = '#D6EAF8'
EXCEL_HIGH_SUSPICION_COLOR = '#F1948A'
EXCEL_MEDIUM_SUSPICION_COLOR = '#F9E79F'
EXCEL_LOW_SUSPICION_COLOR = '#ABEBC6'

# Cache settings
CACHE_EXPIRY_HOURS = 24
