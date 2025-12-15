# MAL Bombing Detector

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A sophisticated tool for detecting rating manipulation (vote bombing) on MyAnimeList. Uses statistical analysis to identify suspicious rating patterns that may indicate coordinated voting campaigns.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [CLI Commands](#cli-commands)
- [Detection Methodology](#detection-methodology)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

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
python -m src single 30276    # One Punch Man (by MAL ID)
```

### Compare Multiple Anime

```bash
python -m src compare 5114,9253,38524    # Comma-separated IDs
```

### Export Results

```bash
python -m src analyze --limit 50 --format excel
python -m src analyze --limit 50 --format json --output ./reports
```

## CLI Commands

### `analyze`

Analyze top anime for review bombing.

```bash
python -m src analyze [OPTIONS]
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--limit` | `-n` | Number of top anime to analyze | 50 |
| `--platform` | `-p` | Platform to analyze | myanimelist |
| `--output` | `-o` | Output directory for reports | output/reports |
| `--format` | `-f` | Export format(s), comma-separated | excel,json |
| `--no-cache` | | Disable caching | false |
| `--no-charts` | | Disable chart generation | false |
| `--lang` | `-l` | Output language (en, ru, es, ja, zh, de, fr) | en |
| `--config` | `-c` | Path to configuration file | None |
| `--verbose` | `-v` | Enable verbose output | false |

**Examples:**
```bash
# Analyze top 100 anime with Excel and JSON export
python -m src analyze -n 100 -f excel,json

# Analyze with custom output directory
python -m src analyze --limit 50 --output ./my-reports

# Analyze without cache (fresh data)
python -m src analyze -n 100 --no-cache
```

### `single`

Deep-dive analysis of a single anime.

```bash
python -m src single ANIME_ID [OPTIONS]
```

| Argument/Option | Description | Required |
|-----------------|-------------|----------|
| `ANIME_ID` | MyAnimeList anime ID | Yes |
| `--platform`, `-p` | Platform to use | No |
| `--verbose`, `-v` | Enable verbose output | No |

**Examples:**
```bash
python -m src single 52991    # Frieren
python -m src single 30276 -v # One Punch Man with verbose output
```

### `compare`

Compare bombing metrics between multiple anime.

```bash
python -m src compare IDS [OPTIONS]
```

| Argument/Option | Description | Required |
|-----------------|-------------|----------|
| `IDS` | Comma-separated anime IDs | Yes |
| `--platform`, `-p` | Platform to use | No |

**Examples:**
```bash
python -m src compare 52991,57555,5114
python -m src compare 30276,9253,38524
```

### `version`

Display version information.

```bash
python -m src version
```

## Detection Methodology

### Metrics Used

| Metric | Weight | Description |
|--------|--------|-------------|
| Ones Z-Score | 35% | Statistical deviation of 1-star ratings from expected |
| Spike Ratio | 20% | Ratio of 1-star ratings to neighboring scores (2-3) |
| Distribution Effect | 20% | Cohen's d effect size for distribution skewness |
| Bimodality | 15% | Detection of unusual rating peaks (10s and 1s) |
| Entropy Deviation | 10% | Rating distribution uniformity measure |

### Severity Levels

| Level | Score Range | Description |
|-------|-------------|-------------|
| 🔴 CRITICAL | 75+ | Strong evidence of coordinated bombing |
| 🟠 HIGH | 55-74 | Likely bombing detected |
| 🟡 MEDIUM | 35-54 | Possible bombing indicators |
| 🟢 LOW | 0-34 | Normal rating distribution |

### Override Rules

The system applies automatic severity overrides for extreme statistical anomalies:

| Condition | Override |
|-----------|----------|
| Z-Score ≥ 15 | → CRITICAL |
| Z-Score ≥ 10 | → HIGH |
| Spike Ratio ≥ 8 | → HIGH |
| Ones % ≥ 3.5% (for anime with score ≥ 8.5) | → HIGH |
| Spike Ratio ≥ 6 + Ones % ≥ 1.5% | → MEDIUM |

## Configuration

Configuration is loaded from `config/config.yaml`. Copy from `config/config.example.yaml` to get started.

### Key Settings

```yaml
# Analysis settings
analysis:
  # Metric weights (must sum to 1.0)
  metric_weights:
    ones_zscore: 0.35
    spike_anomaly: 0.20
    distribution_effect: 0.20
    bimodality: 0.15
    entropy_deficit: 0.10
  
  # Suspicion level thresholds
  suspicion_thresholds:
    critical: 75
    high: 55
    medium: 35

# Rate limiting
rate_limit:
  min_delay: 0.5      # Minimum delay between requests (seconds)
  max_delay: 5.0      # Maximum delay on rate limit errors
  adaptive: true      # Enable adaptive rate limiting

# Cache settings
cache:
  enabled: true
  ttl_hours: 24       # Cache time-to-live

# Export settings
export:
  output_directory: output/reports
  default_format: excel
```

## Project Structure

```
mal-bombing-detector/
├── src/
│   ├── cli/           # Command-line interface (typer)
│   ├── core/          # Analysis logic, metrics, models
│   ├── exporters/     # Export handlers (Excel, JSON, CSV, HTML)
│   ├── platforms/     # Platform scrapers (MyAnimeList)
│   ├── utils/         # Utilities (cache, config, logging, i18n)
│   └── visualization/ # Charts and themes
├── tests/
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   └── fixtures/      # Test data
├── config/            # Configuration files
├── locales/           # Translation files (7 languages)
├── output/            # Generated reports and charts
└── docs/              # Additional documentation
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_metrics.py

# Run with verbose output
pytest -v
```

## Development

### Install Development Dependencies

```bash
pip install -r requirements-dev.txt
```

### Code Formatting and Linting

```bash
# Format code
ruff format .

# Check and fix linting issues
ruff check --fix .
```

### Pre-commit Hooks (Optional)

```bash
pip install pre-commit
pre-commit install
```

## Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║         MAL BOMBING DETECTOR v1.0                            ║
║         Vote brigading detection for anime platforms         ║
╚══════════════════════════════════════════════════════════════╝

✓ Fetched 100 anime from rankings
Collecting statistics ━━━━━━━━━━━━━━━━━━━━ 100/100 • 0:02:15
✓ Collected stats for 98 anime (2 failed)

================================================================================
TOP 20 ANIME WITH HIGHEST BOMBING SUSPICION
================================================================================

#  1 🟠 Gintama: The Final
     Bombing Score: 67.30 (HIGH)
     Ones: 4.27% | Tens: 45.21%
     Flags: extreme_ones_spike, high_zscore

#  2 🟡 Kaguya-sama: Love is War - Ultra Romantic
     Bombing Score: 42.15 (MEDIUM)
     Ones: 1.82% | Tens: 52.34%
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Quick Start for Contributors

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes and add tests
4. Run tests: `pytest`
5. Run linting: `ruff check .`
6. Commit: `git commit -m "feat: add my feature"`
7. Push and create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for **educational and research purposes only**. Always respect MyAnimeList's Terms of Service and rate limits when using this tool. The developers are not responsible for any misuse or violations of platform policies.

---

Made with ❤️ for the anime community
