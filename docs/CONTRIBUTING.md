# Contributing to MAL Review Bombing Analyzer

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Be kind to other contributors and users.

## How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include**:
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/logs

### Suggesting Features

1. **Open a discussion** first for major features
2. **Explain the use case** and why it would benefit users
3. **Consider implementation** complexity and maintenance

### Submitting Code

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write/update tests**
5. **Run the test suite**:
   ```bash
   pytest
   ```
6. **Format your code**:
   ```bash
   black src tests
   isort src tests
   ```
7. **Create a pull request**

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### Environment Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/mal-review-bombing-analyzer.git
cd mal-review-bombing-analyzer

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Copy configuration
cp config/config.example.yaml config/config.yaml
```

### Running Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_metrics.py -v

# Run only fast tests
pytest -m "not slow"
```

### Code Quality Tools

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Type checking
mypy src

# Linting
flake8 src tests

# Security check
bandit -r src

# All checks (via pre-commit)
pre-commit run --all-files
```

## Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://github.com/psf/black) for formatting
- Maximum line length: 88 characters (Black default)
- Use type hints for all function signatures

### Naming Conventions

- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: `_leading_underscore`

### Documentation

- All public functions/classes must have docstrings
- Use Google-style docstrings:

```python
def calculate_metrics(distribution: ScoreDistribution, score: float) -> BombingMetrics:
    """
    Calculate bombing metrics for an anime.
    
    Args:
        distribution: Score distribution data
        score: MAL score of the anime
        
    Returns:
        Calculated bombing metrics
        
    Raises:
        ValueError: If distribution is empty
    """
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): short description

Longer description if needed.

Fixes #123
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(metrics): add bimodality detection
fix(scraper): handle timeout errors gracefully
docs(readme): update installation instructions
test(analyzer): add edge case tests
```

## Project Structure

```
src/
├── cli/            # Command-line interface
├── core/           # Core analysis logic
├── exporters/      # Export formats
├── platforms/      # Platform adapters
├── utils/          # Utilities
└── visualization/  # Charts and graphs
```

### Adding a New Platform

1. Create `src/platforms/newplatform.py`
2. Inherit from `AnimePlatform` abstract class
3. Implement all required methods
4. Add to `src/platforms/__init__.py`
5. Add tests in `tests/unit/test_platforms.py`

### Adding a New Export Format

1. Create `src/exporters/newformat.py`
2. Inherit from `BaseExporter`
3. Implement `export()` and `export_multiple()`
4. Add to `src/exporters/__init__.py`
5. Add tests in `tests/unit/test_exporters.py`

### Adding a New Metric

1. Add calculation in `src/core/statistics.py` if needed
2. Add to `BombingMetricsCalculator` in `src/core/metrics.py`
3. Update `BombingMetrics` model if new field needed
4. Update `config/config.example.yaml` for weights/thresholds
5. Document in `docs/METRICS.md`
6. Add tests

## Testing Guidelines

### Test Structure

```
tests/
├── conftest.py          # Shared fixtures
├── unit/                # Unit tests
│   ├── test_metrics.py
│   ├── test_models.py
│   └── test_statistics.py
└── integration/         # Integration tests
    └── test_analyzer.py
```

### Writing Tests

- Use `pytest` framework
- Group related tests in classes
- Use descriptive test names: `test_calculate_zscore_with_empty_data`
- Use fixtures for common setup
- Test edge cases and error conditions

```python
class TestMetricsCalculator:
    @pytest.fixture
    def calculator(self):
        return BombingMetricsCalculator()
    
    def test_normal_distribution_low_suspicion(self, calculator):
        """Normal distribution should have low suspicion score."""
        result = calculator.calculate(normal_distribution)
        assert result.suspicion_score < 0.3
    
    def test_empty_distribution_handled(self, calculator):
        """Empty distribution should not raise error."""
        result = calculator.calculate(empty_distribution)
        assert result.is_reliable is False
```

## Pull Request Process

1. **Update documentation** if needed
2. **Add/update tests** for your changes
3. **Ensure all tests pass**
4. **Update CHANGELOG.md** if applicable
5. **Request review** from maintainers
6. **Address feedback** promptly
7. **Squash commits** if requested

### PR Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted with Black
- [ ] Type hints added
- [ ] No linting errors
- [ ] CHANGELOG updated (for user-facing changes)

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a git tag: `git tag v1.2.3`
4. Push tag: `git push origin v1.2.3`
5. GitHub Actions will build and publish

## Questions?

- Open a GitHub Discussion for questions
- Check existing issues and discussions
- Join our community chat (if available)

Thank you for contributing! 🎉
