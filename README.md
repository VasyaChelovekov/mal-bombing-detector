# MAL Bombing Detector

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A sophisticated tool for detecting and analyzing review bombing patterns on MyAnimeList (MAL). Uses statistical analysis and machine learning techniques to identify coordinated rating manipulation.

> **Repository**: [github.com/VasyaChelovekov/mal-bombing-detector](https://github.com/VasyaChelovekov/mal-bombing-detector)

## Features

- 🔍 **Multi-factor Detection Algorithm** - Combines Z-scores, effect sizes, entropy analysis, and bimodality detection
- 📊 **Comprehensive Visualization** - Distribution charts, heatmaps, correlation analysis
- 📈 **Multiple Export Formats** - Excel, JSON, CSV, HTML reports
- 🌐 **Internationalization** - 7 languages supported (English, Russian, Spanish, Japanese, Chinese, German, French)
- ⚡ **Async Scraping** - Fast, rate-limited data collection
- 🔧 **Highly Configurable** - YAML configuration for all thresholds and weights
- 🧪 **Well Tested** - Comprehensive unit and integration tests

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/VasyaChelovekov/mal-bombing-detector.git
cd mal-bombing-detector

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config/config.example.yaml config/config.yaml
```

### Basic Usage

```bash
# Analyze top 100 anime
mal-analyzer analyze --top 100

# Analyze a single anime
mal-analyzer single 5114  # Fullmetal Alchemist: Brotherhood

# Compare multiple anime
mal-analyzer compare 5114 1735 28977

# Batch analysis from file
mal-analyzer batch anime_ids.txt
```

### Python API

```python
import asyncio
from src.core.analyzer import BombingAnalyzer
from src.core.models import SuspicionLevel
from src.platforms import get_platform

async def analyze_top_anime():
    # Initialize platform and analyzer
    platform = get_platform("myanimelist")
    analyzer = BombingAnalyzer()
    
    async with platform:
        # Fetch top anime
        top_anime = await platform.get_top_anime(limit=100)
        
        # Get stats and analyze
        anime_list = []
        for anime in top_anime:
            stats = await platform.get_anime_stats(anime.mal_id)
            if stats and stats.distribution:
                anime_list.append(stats)
        
        # Analyze batch
        results = analyzer.analyze_batch(anime_list)
        
        # Process results
        for metrics in results.metrics:
            if metrics.suspicion_level in [SuspicionLevel.CRITICAL, SuspicionLevel.HIGH]:
                print(f"{metrics.title}: {metrics.bombing_score:.2f}")

# Run
asyncio.run(analyze_top_anime())
```

## Project Structure

```
mal-bombing-detector/
├── config/
│   └── config.example.yaml     # Configuration template
├── locales/
│   ├── en.json                 # English translations
│   ├── ru.json                 # Russian translations
│   ├── es.json                 # Spanish translations
│   ├── ja.json                 # Japanese translations
│   ├── zh.json                 # Chinese translations
│   ├── de.json                 # German translations
│   └── fr.json                 # French translations
├── src/
│   ├── cli/                    # Command-line interface
│   ├── core/                   # Core analysis logic
│   │   ├── analyzer.py         # Main orchestrator
│   │   ├── metrics.py          # Bombing metrics calculator
│   │   ├── models.py           # Data models
│   │   └── statistics.py       # Statistical utilities
│   ├── exporters/              # Export formats
│   │   ├── excel.py
│   │   ├── json_export.py
│   │   ├── csv_export.py
│   │   └── html_export.py
│   ├── platforms/              # Platform adapters
│   │   ├── base.py             # Abstract interface
│   │   └── myanimelist.py      # MAL implementation
│   ├── utils/                  # Utilities
│   │   ├── cache.py
│   │   ├── config.py
│   │   ├── i18n.py
│   │   └── logging.py
│   └── visualization/          # Chart generation
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   └── METRICS.md              # Metrics documentation
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Detection Algorithm

The analyzer uses a multi-factor approach to detect review bombing:

### Primary Metrics

| Metric | Description | Weight |
|--------|-------------|--------|
| **Ones Z-Score** | Statistical deviation of 1-votes from expected | 25% |
| **Spike Ratio** | Ratio of 1-votes to neighboring scores | 20% |
| **Distribution Effect Size** | Cohen's d comparing actual vs expected distribution | 20% |
| **Entropy Deficit** | Information entropy reduction from uniform | 15% |
| **Bimodality Index** | Degree of polarization (1s and 10s) | 10% |
| **Contextual Factors** | Member count, age adjustments | 10% |

### Severity Levels

| Level | Score Range | Interpretation |
|-------|-------------|----------------|
| 🔴 Critical | ≥ 0.80 | Clear evidence of coordinated bombing |
| 🟠 High | 0.65 - 0.79 | Strong indicators of manipulation |
| 🟡 Moderate | 0.50 - 0.64 | Suspicious patterns detected |
| 🟢 Low | 0.35 - 0.49 | Minor anomalies |
| 🔵 Minimal | 0.20 - 0.34 | Within normal variation |
| ⚪ None | < 0.20 | No evidence of bombing |

## Configuration

All settings are configurable via `config/config.yaml`:

```yaml
analysis:
  metrics:
    weights:
      ones_zscore: 0.25
      spike_ratio: 0.20
      distribution_effect_size: 0.20
      entropy_deficit: 0.15
      bimodality: 0.10
      contextual: 0.10
    
    thresholds:
      severity:
        critical: 0.80
        high: 0.65
        moderate: 0.50
        low: 0.35
        minimal: 0.20

scraping:
  rate_limit:
    requests_per_second: 1.0
    burst_limit: 5
  
  timeout: 30
  max_retries: 3

output:
  directory: "./output"
  formats:
    - excel
    - json
```

## Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_metrics.py
```

### Code Quality

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Type checking
mypy src

# Linting
flake8 src tests
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

- [ ] AniList platform support
- [ ] Kitsu platform support
- [ ] Machine learning model for improved detection
- [ ] Web interface (Streamlit/Gradio)
- [ ] API server mode
- [ ] Docker support
- [ ] Scheduled analysis with notifications

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- MyAnimeList for providing the data
- The anime community for reporting suspicious patterns
- Contributors and testers

## Disclaimer

This tool is for research and educational purposes only. Always respect MyAnimeList's Terms of Service and API usage policies. The detection algorithm provides statistical indicators, not definitive proof of manipulation.
