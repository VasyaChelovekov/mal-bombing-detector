# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial open-source release

## [2.0.0] - 2024-12-XX

### Added
- Complete project restructure for open-source release
- Multi-factor detection algorithm with 6 complementary metrics
- Async scraping with aiohttp for improved performance
- Platform abstraction layer for future multi-platform support
- Comprehensive CLI with Typer (analyze, single, compare, batch commands)
- Multiple export formats: Excel, JSON, CSV, TSV, HTML
- Internationalization support (English, Russian)
- YAML-based configuration system
- Visualization module with multiple chart types
- Pre-commit hooks for code quality
- GitHub Actions CI/CD pipeline
- Comprehensive documentation (README, METRICS.md, CONTRIBUTING.md)

### Changed
- Rewrote metrics calculation with scientifically-grounded approach
- Removed legacy ERR and RDM metrics
- Replaced with Z-score, effect size, entropy, and bimodality metrics
- All code converted to English (variables, comments, docstrings)
- Improved severity classification thresholds
- Enhanced Excel export with better formatting

### Removed
- Hardcoded Russian text
- Hardcoded configuration values
- Legacy synchronous scraping

### Fixed
- JSON cache key conversion (string to int)
- Excel merged cell handling
- HTML parsing for vote extraction

## [1.0.0] - 2024-12-14

### Added
- Initial version with basic review bombing detection
- MAL scraping functionality
- Excel and CSV export
- Basic visualization
- Russian language interface

---

[Unreleased]: https://github.com/VasyaChelovekov/mal-bombing-detector/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/VasyaChelovekov/mal-bombing-detector/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/VasyaChelovekov/mal-bombing-detector/releases/tag/v1.0.0
