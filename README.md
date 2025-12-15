# MAL Bombing Detector# MAL Bombing Detector# MAL Bombing Detector



[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)



A sophisticated tool for detecting and analyzing review bombing patterns on MyAnimeList (MAL). Uses statistical analysis to identify coordinated rating manipulation.[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)



> **Repository**: [github.com/VasyaChelovekov/mal-bombing-detector](https://github.com/VasyaChelovekov/mal-bombing-detector)[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)



## Features



- 🔍 **Multi-factor Detection Algorithm** - Combines Z-scores, spike ratios, entropy analysis, and bimodality detectionA sophisticated tool for detecting and analyzing review bombing patterns on MyAnimeList (MAL). Uses statistical analysis to identify coordinated rating manipulation.A sophisticated tool for detecting and analyzing review bombing patterns on MyAnimeList (MAL). Uses statistical analysis and machine learning techniques to identify coordinated rating manipulation.

- 📊 **Comprehensive Visualization** - Distribution charts, heatmaps, correlation analysis

- 📈 **Multiple Export Formats** - Excel, JSON, CSV, HTML reports

- 🌐 **Internationalization** - 7 languages supported (en, ru, es, ja, zh, de, fr)

- ⚡ **Async Scraping** - Fast, rate-limited data collection with adaptive delays> **Repository**: [github.com/VasyaChelovekov/mal-bombing-detector](https://github.com/VasyaChelovekov/mal-bombing-detector)> **Repository**: [github.com/VasyaChelovekov/mal-bombing-detector](https://github.com/VasyaChelovekov/mal-bombing-detector)

- 🔧 **Highly Configurable** - YAML configuration for all thresholds and weights

- 🧪 **Well Tested** - 44 unit and integration tests



## Quick Start## Features## Features



### Installation



```bash- 🔍 **Multi-factor Detection Algorithm** - Combines Z-scores, spike ratios, entropy analysis, and bimodality detection- 🔍 **Multi-factor Detection Algorithm** - Combines Z-scores, effect sizes, entropy analysis, and bimodality detection

# Clone the repository

git clone https://github.com/VasyaChelovekov/mal-bombing-detector.git- 📊 **Comprehensive Visualization** - Distribution charts, heatmaps, correlation analysis- 📊 **Comprehensive Visualization** - Distribution charts, heatmaps, correlation analysis

cd mal-bombing-detector

- 📈 **Multiple Export Formats** - Excel, JSON, CSV, HTML reports- 📈 **Multiple Export Formats** - Excel, JSON, CSV, HTML reports

# Create virtual environment

python -m venv .venv- 🌐 **Internationalization** - 7 languages supported (en, ru, es, ja, zh, de, fr)- 🌐 **Internationalization** - 7 languages supported (English, Russian, Spanish, Japanese, Chinese, German, French)

.venv\Scripts\activate  # Windows

# source .venv/bin/activate  # Linux/macOS- ⚡ **Async Scraping** - Fast, rate-limited data collection with adaptive delays- ⚡ **Async Scraping** - Fast, rate-limited data collection



# Install dependencies- 🔧 **Highly Configurable** - YAML configuration for all thresholds and weights- 🔧 **Highly Configurable** - YAML configuration for all thresholds and weights

pip install -r requirements.txt

- 🧪 **Well Tested** - 44 unit and integration tests- 🧪 **Well Tested** - Comprehensive unit and integration tests

# Copy configuration

cp config/config.example.yaml config/config.yaml

```

## Quick Start## Quick Start

### CLI Usage



```bash

# Analyze top 100 anime### Installation### Installation

python -m src analyze -n 100



# Analyze with specific output format

python -m src analyze --limit 50 --format excel,json```bash```bash



# Analyze and save to custom directory# Clone the repository# Clone the repository

python -m src analyze -n 100 -o ./reports -f json

git clone https://github.com/VasyaChelovekov/mal-bombing-detector.gitgit clone https://github.com/VasyaChelovekov/mal-bombing-detector.git

# Analyze a single anime by ID

python -m src single 5114  # Fullmetal Alchemist: Brotherhoodcd mal-bombing-detectorcd mal-bombing-detector



# Compare multiple anime

python -m src compare 5114,1735,28977

# Create virtual environment# Create virtual environment

# Show version

python -m src versionpython -m venv .venvpython -m venv .venv

```

.venv\Scripts\activate  # Windows.venv\Scripts\activate  # Windows

### Python API

# source .venv/bin/activate  # Linux/macOS# source .venv/bin/activate  # Linux/macOS

```python

import asyncio

from src.core.analyzer import BombingAnalyzer

from src.core.models import SuspicionLevel# Install dependencies# Install dependencies

from src.platforms import get_platform

pip install -r requirements.txtpip install -r requirements.txt

async def analyze_top_anime():

    platform = get_platform("myanimelist")

    analyzer = BombingAnalyzer()

    # Copy configuration# Copy configuration

    async with platform:

        # Fetch top animecp config/config.example.yaml config/config.yamlcp config/config.example.yaml config/config.yaml

        top_anime = await platform.get_top_anime(limit=100)

        ``````

        # Get stats and analyze

        anime_list = []

        for anime in top_anime:

            stats = await platform.get_anime_stats(anime.mal_id)### CLI Usage### Basic Usage

            if stats and stats.distribution:

                # Use score from top list if stats page didn't have it

                if stats.score == 0.0 and anime.score > 0:

                    stats.score = anime.score```bash```bash

                anime_list.append(stats)

        # Analyze top 100 anime# Analyze top 100 anime

        # Analyze batch

        results = analyzer.analyze_batch(anime_list)python -m src analyze -n 100mal-analyzer analyze --top 100

        

        # Process results - get top 20 by bombing score

        for metrics in results.get_top(20):

            if metrics.suspicion_level in [SuspicionLevel.CRITICAL, SuspicionLevel.HIGH]:# Analyze with specific output format# Analyze a single anime

                print(f"{metrics.title}: {metrics.bombing_score:.2f} ({metrics.suspicion_level.value})")

python -m src analyze --limit 50 --format excel,jsonmal-analyzer single 5114  # Fullmetal Alchemist: Brotherhood

asyncio.run(analyze_top_anime())

```



## Project Structure# Analyze and save to custom directory# Compare multiple anime



```python -m src analyze -n 100 -o ./reports -f jsonmal-analyzer compare 5114 1735 28977

mal-bombing-detector/

├── config/

│   ├── config.example.yaml     # Configuration template

│   └── config.yaml             # Your configuration (gitignored)# Analyze a single anime by ID# Batch analysis from file

├── locales/                    # Translations (en, ru, es, ja, zh, de, fr)

├── src/python -m src single 5114  # Fullmetal Alchemist: Brotherhoodmal-analyzer batch anime_ids.txt

│   ├── __main__.py             # Entry point for python -m src

│   ├── cli/                    # Command-line interface (typer + rich)```

│   ├── core/                   # Core analysis logic

│   │   ├── analyzer.py         # Main orchestrator# Compare multiple anime

│   │   ├── metrics.py          # Bombing metrics calculator

│   │   ├── models.py           # Data modelspython -m src compare 5114,1735,28977### Python API

│   │   └── statistics.py       # Statistical utilities

│   ├── exporters/              # Export formats (excel, json, csv, html)

│   ├── platforms/              # Platform adapters

│   │   ├── base.py             # Abstract interface# Show version```python

│   │   └── myanimelist.py      # MAL scraper implementation

│   ├── utils/                  # Utilities (cache, config, i18n, logging)python -m src versionimport asyncio

│   └── visualization/          # Chart generation

├── tests/```from src.core.analyzer import BombingAnalyzer

│   ├── unit/                   # Unit tests

│   └── integration/            # Integration testsfrom src.core.models import SuspicionLevel

├── output/                     # Generated reports (gitignored)

├── pyproject.toml### Python APIfrom src.platforms import get_platform

├── requirements.txt

└── README.md

```

```pythonasync def analyze_top_anime():

## Detection Algorithm

import asyncio    # Initialize platform and analyzer

The analyzer uses a multi-factor approach to detect review bombing:

from src.core.analyzer import BombingAnalyzer    platform = get_platform("myanimelist")

### Primary Metrics

from src.core.models import SuspicionLevel    analyzer = BombingAnalyzer()

| Metric | Description | Weight |

|--------|-------------|--------|from src.platforms import get_platform    

| **Ones Z-Score** | Statistical deviation of 1-votes from expected for rating category | 35% |

| **Spike Ratio** | Ratio of 1-votes to 2-votes (natural ratio ≈ 1:1) | 20% |    async with platform:

| **Distribution Effect** | Cohen's d comparing actual vs expected distribution | 20% |

| **Bimodality Index** | Degree of polarization (1s and 10s concentration) | 15% |async def analyze_top_anime():        # Fetch top anime

| **Entropy Deficit** | Information entropy reduction from uniform distribution | 10% |

    platform = get_platform("myanimelist")        top_anime = await platform.get_top_anime(limit=100)

### Suspicion Levels

    analyzer = BombingAnalyzer()        

| Level | Score | Interpretation |

|-------|-------|----------------|            # Get stats and analyze

| 🔴 **Critical** | ≥ 75 | Clear evidence of coordinated bombing |

| 🟠 **High** | 55 - 74 | Strong indicators of manipulation |    async with platform:        anime_list = []

| 🟡 **Medium** | 35 - 54 | Suspicious patterns detected |

| 🟢 **Low** | < 35 | Within normal variation |        # Fetch top anime        for anime in top_anime:



### Override Rules        top_anime = await platform.get_top_anime(limit=100)            stats = await platform.get_anime_stats(anime.mal_id)



The algorithm applies direct overrides for extreme statistical anomalies:                    if stats and stats.distribution:



- **Z-score ≥ 15** → Critical (regardless of composite score)        # Get stats and analyze                anime_list.append(stats)

- **Z-score ≥ 10** → High

- **Spike ratio ≥ 8** → High        anime_list = []        

- **Ones% ≥ 3.5%** on highly-rated anime → High

        for anime in top_anime:        # Analyze batch

## Configuration

            stats = await platform.get_anime_stats(anime.mal_id)        results = analyzer.analyze_batch(anime_list)

All settings are configurable via `config/config.yaml`:

            if stats and stats.distribution:        

```yaml

analysis:                # Merge score from top list if needed        # Process results

  min_votes_threshold: 1000

                  if stats.score == 0.0 and anime.score > 0:        for metrics in results.metrics:

  # Expected ones% by rating category

  expected_ones_by_rating:                    stats.score = anime.score            if metrics.suspicion_level in [SuspicionLevel.CRITICAL, SuspicionLevel.HIGH]:

    elite:     # score >= 9.0

      mean: 0.4                anime_list.append(stats)                print(f"{metrics.title}: {metrics.bombing_score:.2f}")

      std: 0.25

    excellent: # score >= 8.5        

      mean: 0.7

      std: 0.35        # Analyze batch# Run

    great:     # score >= 8.0

      mean: 1.2        results = analyzer.analyze_batch(anime_list)asyncio.run(analyze_top_anime())

      std: 0.5

        ```

scraping:

  timeout: 30        # Process results - get top 20 by bombing score

  max_retries: 3

  retry_delay: 2.0        for metrics in results.get_top(20):## Project Structure

  

  adaptive_delay:            if metrics.suspicion_level in [SuspicionLevel.CRITICAL, SuspicionLevel.HIGH]:

    enabled: true

    min_delay: 0.5                print(f"{metrics.title}: {metrics.bombing_score:.2f} ({metrics.suspicion_level.value})")```

    max_delay: 5.0

    success_threshold: 5mal-bombing-detector/



output:asyncio.run(analyze_top_anime())├── config/

  directory: "./output"

  cache_directory: "./data/cache"```│   └── config.example.yaml     # Configuration template



logging:├── locales/

  level: "INFO"

  file: "output/analysis.log"## Project Structure│   ├── en.json                 # English translations

```

│   ├── ru.json                 # Russian translations

## Development

```│   ├── es.json                 # Spanish translations

### Setup Development Environment

mal-bombing-detector/│   ├── ja.json                 # Japanese translations

```bash

# Install dev dependencies├── config/│   ├── zh.json                 # Chinese translations

pip install -r requirements-dev.txt

```│   ├── config.example.yaml     # Configuration template│   ├── de.json                 # German translations



### Running Tests│   └── config.yaml             # Your configuration (gitignored)│   └── fr.json                 # French translations



```bash├── locales/                    # Translations (en, ru, es, ja, zh, de, fr)├── src/

# All tests

pytest├── src/│   ├── cli/                    # Command-line interface



# With coverage│   ├── __main__.py             # Entry point for python -m src│   ├── core/                   # Core analysis logic

pytest --cov=src --cov-report=html

│   ├── cli/                    # Command-line interface (typer)│   │   ├── analyzer.py         # Main orchestrator

# Specific test file

pytest tests/unit/test_metrics.py -v│   ├── core/                   # Core analysis logic│   │   ├── metrics.py          # Bombing metrics calculator

```

│   │   ├── analyzer.py         # Main orchestrator│   │   ├── models.py           # Data models

### Code Quality

│   │   ├── metrics.py          # Bombing metrics calculator│   │   └── statistics.py       # Statistical utilities

```bash

# Lint and auto-fix│   │   ├── models.py           # Data models│   ├── exporters/              # Export formats

ruff check --fix

│   │   └── statistics.py       # Statistical utilities│   │   ├── excel.py

# Type checking

mypy src│   ├── exporters/              # Export formats (excel, json, csv, html)│   │   ├── json_export.py

```

│   ├── platforms/              # Platform adapters│   │   ├── csv_export.py

## Contributing

│   │   ├── base.py             # Abstract interface│   │   └── html_export.py

Contributions are welcome! Please follow these guidelines:

│   │   └── myanimelist.py      # MAL implementation│   ├── platforms/              # Platform adapters

1. Fork the repository

2. Create a feature branch (`git checkout -b feature/amazing-feature`)│   ├── utils/                  # Utilities (cache, config, i18n, logging)│   │   ├── base.py             # Abstract interface

3. Write tests for your changes

4. Ensure all tests pass (`pytest`)│   └── visualization/          # Chart generation│   │   └── myanimelist.py      # MAL implementation

5. Ensure code is linted (`ruff check`)

6. Commit with conventional messages (`feat: add amazing feature`)├── tests/│   ├── utils/                  # Utilities

7. Push to the branch (`git push origin feature/amazing-feature`)

8. Open a Pull Request│   ├── unit/                   # Unit tests│   │   ├── cache.py



## Roadmap│   └── integration/            # Integration tests│   │   ├── config.py



- [ ] AniList platform support├── output/                     # Generated reports (gitignored)│   │   ├── i18n.py

- [ ] Kitsu platform support

- [ ] Web interface (Streamlit/Gradio)├── pyproject.toml│   │   └── logging.py

- [ ] Docker support

- [ ] Scheduled analysis with notifications├── requirements.txt│   └── visualization/          # Chart generation



## License└── README.md├── tests/



This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.```│   ├── unit/



## Disclaimer│   └── integration/



This tool is for research and educational purposes only. Always respect MyAnimeList's Terms of Service and rate limits. The detection algorithm provides statistical indicators, not definitive proof of manipulation.## Detection Algorithm├── docs/


│   └── METRICS.md              # Metrics documentation

The analyzer uses a multi-factor approach to detect review bombing:├── pyproject.toml

├── requirements.txt

### Primary Metrics└── README.md

```

| Metric | Description | Weight |

|--------|-------------|--------|## Detection Algorithm

| **Ones Z-Score** | Statistical deviation of 1-votes from expected for rating category | 35% |

| **Spike Ratio** | Ratio of 1-votes to 2-votes (natural ratio ≈ 1:1) | 20% |The analyzer uses a multi-factor approach to detect review bombing:

| **Distribution Effect** | Cohen's d comparing actual vs expected distribution | 20% |

| **Bimodality Index** | Degree of polarization (1s and 10s concentration) | 15% |### Primary Metrics

| **Entropy Deficit** | Information entropy reduction from uniform distribution | 10% |

| Metric | Description | Weight |

### Suspicion Levels|--------|-------------|--------|

| **Ones Z-Score** | Statistical deviation of 1-votes from expected | 25% |

| Level | Score | Interpretation || **Spike Ratio** | Ratio of 1-votes to neighboring scores | 20% |

|-------|-------|----------------|| **Distribution Effect Size** | Cohen's d comparing actual vs expected distribution | 20% |

| 🔴 **Critical** | ≥ 75 | Clear evidence of coordinated bombing || **Entropy Deficit** | Information entropy reduction from uniform | 15% |

| 🟠 **High** | 55 - 74 | Strong indicators of manipulation || **Bimodality Index** | Degree of polarization (1s and 10s) | 10% |

| 🟡 **Medium** | 35 - 54 | Suspicious patterns detected || **Contextual Factors** | Member count, age adjustments | 10% |

| 🟢 **Low** | < 35 | Within normal variation |

### Severity Levels

### Override Rules

| Level | Score Range | Interpretation |

The algorithm also applies direct overrides for extreme anomalies:|-------|-------------|----------------|

| 🔴 Critical | ≥ 0.80 | Clear evidence of coordinated bombing |

- **Z-score ≥ 15** → Critical (regardless of composite score)| 🟠 High | 0.65 - 0.79 | Strong indicators of manipulation |

- **Z-score ≥ 10** → High| 🟡 Moderate | 0.50 - 0.64 | Suspicious patterns detected |

- **Spike ratio ≥ 8** → High| 🟢 Low | 0.35 - 0.49 | Minor anomalies |

- **Ones% ≥ 3.5%** on highly-rated anime → High| 🔵 Minimal | 0.20 - 0.34 | Within normal variation |

| ⚪ None | < 0.20 | No evidence of bombing |

## Configuration

## Configuration

All settings are configurable via `config/config.yaml`:

All settings are configurable via `config/config.yaml`:

```yaml

analysis:```yaml

  min_votes_threshold: 1000analysis:

    metrics:

  # Expected ones% by rating category    weights:

  expected_ones_by_rating:      ones_zscore: 0.25

    elite:     # score >= 9.0      spike_ratio: 0.20

      mean: 0.4      distribution_effect_size: 0.20

      std: 0.25      entropy_deficit: 0.15

    excellent: # score >= 8.5      bimodality: 0.10

      mean: 0.7      contextual: 0.10

      std: 0.35    

    great:     # score >= 8.0    thresholds:

      mean: 1.2      severity:

      std: 0.5        critical: 0.80

        high: 0.65

scraping:        moderate: 0.50

  timeout: 30        low: 0.35

  max_retries: 3        minimal: 0.20

  retry_delay: 2.0

  scraping:

  adaptive_delay:  rate_limit:

    enabled: true    requests_per_second: 1.0

    min_delay: 0.5    burst_limit: 5

    max_delay: 5.0  

    success_threshold: 5  timeout: 30

  max_retries: 3

output:

  directory: "./output"output:

  cache_directory: "./data/cache"  directory: "./output"

  formats:

logging:    - excel

  level: "INFO"    - json

  file: "output/analysis.log"```

```

## Development

## Development

### Setup Development Environment

### Setup Development Environment

```bash

```bash# Install dev dependencies

# Install dev dependenciespip install -r requirements-dev.txt

pip install -r requirements-dev.txt

```# Install pre-commit hooks

pre-commit install

### Running Tests```



```bash### Running Tests

# All tests

pytest```bash

# All tests

# With coveragepytest

pytest --cov=src --cov-report=html

# With coverage

# Specific test filepytest --cov=src --cov-report=html

pytest tests/unit/test_metrics.py -v

```# Specific test file

pytest tests/unit/test_metrics.py

### Code Quality```



```bash### Code Quality

# Lint and auto-fix

ruff check --fix```bash

# Format code

# Format code (if using black)black src tests

black src tests

# Sort imports

# Type checkingisort src tests

mypy src

```# Type checking

mypy src

## Contributing

# Linting

Contributions are welcome! Please follow these guidelines:flake8 src tests

```

1. Fork the repository

2. Create a feature branch (`git checkout -b feature/amazing-feature`)## Contributing

3. Write tests for your changes

4. Ensure all tests pass (`pytest`)Contributions are welcome! Please see [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

5. Ensure code is linted (`ruff check`)

6. Commit with conventional messages (`feat: add amazing feature`)1. Fork the repository

7. Push to the branch (`git push origin feature/amazing-feature`)2. Create a feature branch (`git checkout -b feature/amazing-feature`)

8. Open a Pull Request3. Commit your changes (`git commit -m 'Add amazing feature'`)

4. Push to the branch (`git push origin feature/amazing-feature`)

## Roadmap5. Open a Pull Request



- [ ] AniList platform support## Roadmap

- [ ] Kitsu platform support

- [ ] Web interface (Streamlit/Gradio)- [ ] AniList platform support

- [ ] Docker support- [ ] Kitsu platform support

- [ ] Scheduled analysis with notifications- [ ] Machine learning model for improved detection

- [ ] Web interface (Streamlit/Gradio)

## License- [ ] API server mode

- [ ] Docker support

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.- [ ] Scheduled analysis with notifications



## Disclaimer## License



This tool is for research and educational purposes only. Always respect MyAnimeList's Terms of Service and rate limits. The detection algorithm provides statistical indicators, not definitive proof of manipulation.This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## Acknowledgments

- MyAnimeList for providing the data
- The anime community for reporting suspicious patterns
- Contributors and testers

## Disclaimer

This tool is for research and educational purposes only. Always respect MyAnimeList's Terms of Service and API usage policies. The detection algorithm provides statistical indicators, not definitive proof of manipulation.
