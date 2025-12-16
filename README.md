# MAL Bombing Detector

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

**Detect rating manipulation (vote bombing) on MyAnimeList using statistical analysis.**

The tool fetches anime rating distributions and applies multiple statistical metrics to surface suspicious patterns that may indicate coordinated 1-star campaigns.

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [CLI Reference](#cli-reference)
  - [analyze](#analyze)
  - [single](#single)
  - [compare](#compare)
  - [version](#version)
- [Configuration](#configuration)
  - [Precedence Rules](#precedence-rules)
  - [Output Directory Semantics](#output-directory-semantics)
- [Export Formats](#export-formats)
- [Detection Methodology](#detection-methodology)
- [Development & Testing](#development--testing)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Statistical Detection** — Z-score analysis, spike ratios, Cohen's d effect size, bimodality, entropy deficit
- **Multiple Export Formats** — Excel, JSON, CSV, HTML
- **Multi-Language Output** — en, ja, de, fr, es, ru, zh
- **Caching** — Reduces API calls on repeated runs
- **Rich CLI** — Progress bars, colored output, and structured reports

---

## Installation

**Requirements:** Python 3.10+

```bash
# Clone the repository
git clone https://github.com/VasyaChelovekov/mal-bombing-detector.git
cd mal-bombing-detector

# Install dependencies
pip install -r requirements.txt

# (Optional) Copy the example config
cp config/config.example.yaml config/config.yaml
```

---

## Quickstart

### Analyze the top 100 anime

```bash
python -m src analyze --limit 100
```

Output files are written to `output/reports/` by default (e.g., `top_100_analysis_20251216_120000.xlsx`).

### Analyze a single anime by MAL ID

```bash
python -m src single 30276
```

Prints a detailed metric breakdown for the specified anime (e.g., One Punch Man).

### Compare multiple anime

```bash
python -m src compare 5114,9253,38524
```

Displays a side-by-side comparison table.

### Check version

```bash
python -m src version
```

Prints `MAL Bombing Detector v<version>` using the packaged `__version__` from `src/_version.py`.

---

## CLI Reference

### `analyze`

Analyze top N anime for review bombing.

```bash
python -m src analyze [OPTIONS]
```

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--limit` | `-n` | Number of top anime to analyze | `50` |
| `--platform` | `-p` | Platform to analyze | config `platforms.default` or `myanimelist` |
| `--output` | `-o` | Output directory for reports (treated as final path) | config `export.output_directory` + `/reports` if needed |
| `--format` | `-f` | Export format(s), comma-separated | config `export.default_format` or `excel,json` |
| `--no-cache` | | Disable caching | `false` |
| `--no-charts` | | Disable chart generation | `false` |
| `--lang` | `-l` | Output language (en, ru, es, ja, zh, de, fr) | config `general.language` or `en` |
| `--config` | `-c` | Path to configuration file | `config/config.yaml` |
| `--verbose` | `-v` | Enable verbose output | `false` |

**Examples:**

```bash
# Analyze top 100 anime, export to Excel and JSON
python -m src analyze -n 100 -f excel,json

# Analyze with explicit output directory (no automatic suffix)
python -m src analyze --limit 50 --output C:/tmp/run

# Analyze in Japanese, skip cache
python -m src analyze -n 100 --lang ja --no-cache
```

---

### `single`

Deep-dive analysis of a single anime.

```bash
python -m src single ANIME_ID [OPTIONS]
```

| Argument/Option | Description |
|-----------------|-------------|
| `ANIME_ID` | MyAnimeList anime ID (required) |
| `--platform`, `-p` | Platform override (default from config) |
| `--verbose`, `-v` | Enable verbose output |

**Examples:**

```bash
python -m src single 52991         # Frieren
python -m src single 30276 -v      # One Punch Man with verbose output
```

---

### `compare`

Compare bombing metrics between multiple anime.

```bash
python -m src compare IDS [OPTIONS]
```

| Argument/Option | Description |
|-----------------|-------------|
| `IDS` | Comma-separated anime IDs (required) |
| `--platform`, `-p` | Platform override (default from config) |

**Examples:**

```bash
python -m src compare 52991,57555,5114
```

---

### `version`

Display version information.

```bash
python -m src version
```

Prints the version string from `src/_version.py`.

---

## Configuration

Copy `config/config.example.yaml` to `config/config.yaml` and edit as needed. Key sections:

```yaml
general:
  language: en          # Output language (en, ru, es, ja, zh, de, fr)
  log_level: INFO

platforms:
  default: myanimelist  # Default platform if --platform not specified

cache:
  enabled: true
  directory: "data/cache"
  expiry_hours: 24

export:
  output_directory: "output/reports"   # Base output path
  default_format: "excel,json"         # Default --format value

analysis:
  metric_weights:
    ones_zscore: 0.35
    spike_anomaly: 0.20
    distribution_effect: 0.20
    bimodality: 0.15
    entropy_deficit: 0.10
  suspicion_thresholds:
    critical: 75
    high: 55
    medium: 35
```

---

### Precedence Rules

Options are resolved in the following order (first defined wins):

| Command | Precedence |
|---------|------------|
| **analyze** | CLI args → config file → built-in defaults |
| **single** | Language: config `general.language`; Platform: CLI `--platform` → config `platforms.default` |
| **compare** | Language: config `general.language`; Platform: CLI `--platform` → config `platforms.default` |

---

### Output Directory Semantics

The tool avoids duplicating `reports` in the output path:

| Scenario | Config / CLI | Resulting output path |
|----------|--------------|----------------------|
| Config base dir | `export.output_directory: output` | `output/reports/top_{n}_analysis_*.{ext}` |
| Config already ends with `reports` | `export.output_directory: output/reports` | `output/reports/top_{n}_analysis_*.{ext}` (no extra suffix) |
| CLI `--output` | `--output C:/tmp/run` | `C:/tmp/run/top_{n}_analysis_*.{ext}` (used as-is, no suffix) |

> **Key rule:** `--output` is treated as the **final directory**—no automatic `reports` suffix is added.

---

## Export Formats

Select formats via `--format` (comma-separated):

| Format | Extension | Description |
|--------|-----------|-------------|
| `excel` | `.xlsx` | Full report with optional charts and severity sheet |
| `json` | `.json` | Machine-readable payload with metadata, summary, results, and failures |
| `csv` | `.csv` | Simple tabular export |
| `html` | `.html` | Styled HTML report (template-based) |

**JSON structure (key fields):**

- `metadata` — `generated_at`, `version`, `language`, totals (`total_requested`, `total_analyzed`, `total_failed`, `total_skipped`, `total_batches`)
- `summary` — `count_by_level`, `suspicious_count`, `highly_suspicious_count`, score statistics
- `results` — per-batch objects with `metrics` and batch-scoped `summary`
- `failures` (optional) — list of `{ mal_id, title, url, stage, error_type, message, timestamp }`

---

## Detection Methodology

### Metrics

| Metric | Weight | Description |
|--------|--------|-------------|
| Ones Z-Score | 35% | How statistically unusual the 1-vote count is |
| Spike Ratio | 20% | Ratio of 1-votes to neighboring scores (2–4) |
| Distribution Effect | 20% | Cohen's d effect size for distribution skewness |
| Bimodality | 15% | Detects dual peaks at 10s and 1s |
| Entropy Deficit | 10% | Measures rating distribution uniformity |

### Bombing Score Adjustments (v1.2.0+)

To reduce false positives on popular anime with naturally high 10-vote counts, the detector applies several adjustments:

#### Minimum Ones Thresholds

Severity levels now require a minimum percentage of 1-votes:

| Level | Min Score | Min Ones % | Rationale |
|-------|-----------|------------|-----------|
| 🔴 CRITICAL | 75 | ≥ 2.0% | Real bombing campaigns produce noticeable 1-vote spikes |
| 🟠 HIGH | 55 | ≥ 1.5% | Anime below this threshold are likely popular, not bombed |

Anime with high scores but insufficient 1-vote percentages are downgraded to MEDIUM or lower.

#### Popularity Discount

When an anime has **tens_percent > 45%** and **ones_percent < 1.5%**, the effect size is multiplied by `0.5`. This prevents popular anime (e.g., Frieren, Steins;Gate) from being flagged due to high 10-vote concentrations.

#### Spike Damping

For anime with low 1-vote percentages, the spike ratio contribution is damped:

| Ones % | Damping Factor |
|--------|----------------|
| ≥ 2.0% | 1.0 (full weight) |
| 0.5–2.0% | Linear scale (0.25 → 1.0) |
| < 0.5% | 0.0 (ignored) |

This ensures that small absolute spikes in 1-votes don't disproportionately affect the score.

### Severity Levels

Levels are determined by the bombing score (0–100) **and ones_percent thresholds**:

| Level | Score Range | Ones % Requirement | Description |
|-------|-------------|-------------------|-------------|
| 🔴 CRITICAL | 75–100 | ≥ 2.0% | Strong evidence of coordinated bombing |
| 🟠 HIGH | 55–74 | ≥ 1.5% | Likely bombing detected |
| 🟡 MEDIUM | 35–54 | — | Possible bombing indicators |
| 🟢 LOW | 0–34 | — | Normal rating distribution |

Anomaly flags (e.g., `extreme_ones_spike`, `high_zscore`) are **informational** and do not override the level.

---

## Development & Testing

### Install dev dependencies

```bash
pip install -r requirements-dev.txt
```

### Code quality

```bash
ruff format .        # Format code
ruff check .         # Lint (add --fix for auto-fix)
pytest -q            # Run tests
```

Tests cover CLI path semantics, exporter payload integrity, config precedence, and failure-record factories.

---

## Troubleshooting

| Problem | Possible Cause | Solution |
|---------|----------------|----------|
| `No distribution data for ID` | Anime stats page unavailable or private | Retry later or skip the ID |
| Double `reports/reports` in path | Older config had trailing `/reports` | Upgrade to latest code; the tool now avoids duplicating the segment |
| Rate-limit errors (429) | Too many requests | Enable adaptive delay in config (`scraping.adaptive_delay.enabled: true`) and increase `min_delay` |
| Missing language strings | Locale file incomplete | Ensure all keys exist in `locales/{lang}.json`; fallback is `en` |
| `--output` ignored | Flag placed after positional arg | Place `--output` before positional arguments |

---

## Contributing

Contributions are welcome! See [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for full guidelines.

**Quick steps:**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run `pytest` and `ruff check .`
5. Commit using conventional commits: `git commit -m "feat: add my feature"`
6. Open a Pull Request

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## Disclaimer

This tool is for **educational and research purposes only**. Always respect MyAnimeList's Terms of Service and rate limits. The developers are not responsible for any misuse or violations of platform policies.

---

Made with ❤️ for the anime community
