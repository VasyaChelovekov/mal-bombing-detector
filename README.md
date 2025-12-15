# MAL Bombing Detector

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A sophisticated tool for detecting rating manipulation (vote bombing) on MyAnimeList. Uses statistical analysis to identify suspicious rating patterns that may indicate coordinated voting campaigns.

## Features

- **Statistical Analysis**: Detects anomalies using z-score analysis, spike ratios, and distribution analysis
- **Multi-Language Support**: Available in English, Japanese, German, French, Spanish, Russian, and Chinese
- **Multiple Export Formats**: Export results to Excel, JSON, CSV, or HTML
- **Caching System**: Efficient caching to reduce API calls and speed up repeated analysis
- **CLI Interface**: Full command-line interface for easy automation
- **Progress Tracking**: Real-time progress bars with time estimates

## Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/VasyaChelovekov/mal-bombing-detector.git
cd mal-bombing-detector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Copy the example config:
```bash
cp config/config.example.yaml config/config.yaml
```

## Quick Start

### Analyze Top Anime

Analyze the top 100 anime by rating:

```bash
python -m src analyze --limit 100
```

### Analyze a Single Anime

```bash
python -m src single 21 --name "One Punch Man"
```

### Compare Multiple Anime

```bash
python -m src compare 21 1735 5114
```

### Export Results

```bash
python -m src analyze --limit 50 --format excel --output results.xlsx
python -m src analyze --limit 50 --format json --output results.json
```

## CLI Commands

### `analyze`
Analyze top anime by rating.

| Option | Description | Default |
|--------|-------------|---------|
| `--limit` | Number of anime to analyze | 50 |
| `--format` | Export format (excel/json/csv/html) | None |
| `--output` | Output file path | None |

### `single`
Analyze a single anime by ID.

| Option | Description | Default |
|--------|-------------|---------|
| `--id` | MyAnimeList anime ID | Required |
| `--name` | Anime name for display | None |

### `compare`
Compare multiple anime.

| Option | Description | Default |
|--------|-------------|---------|
| `IDS` | Space-separated list of anime IDs | Required |

### `version`
Display version information.

## Detection Methodology

### Metrics Used

| Metric | Weight | Description |
|--------|--------|-------------|
| Ones Z-Score | 35% | Statistical deviation of 1-star ratings |
| Spike Ratio | 20% | Ratio of lowest to neighboring ratings |
| Distribution Effect | 20% | Overall distribution skewness |
| Bimodality | 15% | Presence of unusual rating peaks |
| Entropy Deviation | 10% | Rating distribution uniformity |

### Severity Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| CRITICAL | 75+ | Strong evidence of bombing |
| HIGH | 55-74 | Likely bombing detected |
| MEDIUM | 35-54 | Possible bombing indicators |
| LOW | 0-34 | Normal rating distribution |

### Override Rules

The system applies automatic overrides for extreme cases:

- **Z-Score >= 15**: Automatically classified as CRITICAL
- **Z-Score >= 10**: Automatically classified as HIGH
- **Spike Ratio >= 8**: Automatically classified as HIGH
- **Ones Percentage >= 3.5%**: Automatically classified as HIGH

## Configuration

Edit `config/config.yaml` to customize:

```yaml
# Rate limiting
rate_limit:
  min_delay: 0.5      # Minimum delay between requests (seconds)
  max_delay: 5.0      # Maximum delay between requests (seconds)
  adaptive: true      # Enable adaptive rate limiting

# Cache settings
cache:
  enabled: true
  ttl_hours: 24       # Cache time-to-live

# Detection thresholds
thresholds:
  critical: 75
  high: 55
  medium: 35

# Export settings
export:
  default_format: excel
  output_dir: output/reports
```

## Project Structure

```
mal-bombing-detector/
├── src/
│   ├── cli/           # Command-line interface
│   ├── core/          # Analysis logic and metrics
│   ├── exporters/     # Export format handlers
│   ├── platforms/     # Platform scrapers (MAL)
│   ├── utils/         # Utilities (cache, config, logging)
│   └── visualization/ # Charts and themes
├── tests/             # Unit and integration tests
├── config/            # Configuration files
├── locales/           # Translation files
├── output/            # Generated reports
└── docs/              # Documentation
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_metrics.py
```

## Development

### Install dev dependencies

```bash
pip install -r requirements-dev.txt
```

### Code formatting

```bash
ruff format .
ruff check --fix .
```

## Examples

### Sample Output

```
┌─────────────────────────────────────────────────────────────┐
│                   BOMBING ANALYSIS RESULTS                  │
├─────────────────────────────────────────────────────────────┤
│ Anime: Gintama: The Final                                   │
│ Score: 9.05 | Members: 312,847                              │
│ Severity: HIGH (Score: 67.3)                                │
├─────────────────────────────────────────────────────────────┤
│ Metrics:                                                    │
│   - Ones Z-Score: 15.48 (Weight: 35%)                       │
│   - Spike Ratio: 9.93 (Weight: 20%)                         │
│   - Distribution Effect: 0.72 (Weight: 20%)                 │
│   - Bimodality: 0.45 (Weight: 15%)                          │
│   - Entropy Deviation: 0.31 (Weight: 10%)                   │
│                                                             │
│ Detection: 4.27% of votes are 1-star ratings                │
│            (Normal range: 0.5-1.5%)                         │
└─────────────────────────────────────────────────────────────┘
```

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and research purposes only. Always respect MyAnimeList's Terms of Service and rate limits when using this tool.
