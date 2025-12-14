# AI Development Instructions

> Universal guidelines for AI assistants working on this project.
> These instructions are designed to remain valid as the project evolves.

---

## 1. Discovery First

Before making any changes, always discover the current project state:

```bash
# Understand project structure
ls -la src/          # or: Get-ChildItem src/
find . -name "*.py" -type f | head -50

# Find main entry points
cat main.py
cat pyproject.toml   # Check [project.scripts] and dependencies

# Discover module exports
grep -r "^from\|^import" src/__init__.py
grep -r "__all__" src/

# Find test structure
ls tests/
cat tests/conftest.py

# Check for configuration
ls config/ *.yaml *.toml *.json 2>/dev/null
```

**Never assume structure — always verify first.**

---

## 2. Code Style Requirements

### Language
- **All code comments**: English only
- **All docstrings**: English only
- **Variable/function/class names**: English only
- **Git commits**: English only

### Python Standards
- Python 3.10+ syntax (use `|` for unions, not `Union[]`)
- Type hints on all public functions and methods
- Google-style docstrings with Args, Returns, Raises sections
- `snake_case` for functions/variables, `PascalCase` for classes
- `UPPER_CASE` for constants

### Code Organization
- Imports grouped: stdlib → third-party → local (blank line between groups)
- Keep functions under 50 lines when possible
- Prefer composition over inheritance
- Use dataclasses or Pydantic models for data structures

---

## 3. Before Editing Code

1. **Read the file** — understand context before changing
2. **Check imports** — find related modules
3. **Find usages** — search for references to avoid breaking changes
4. **Review tests** — understand expected behavior
5. **Check __init__.py** — see what's publicly exported

```bash
# Find where a class/function is used
grep -rn "ClassName" src/ tests/

# Check what a module exports
head -50 src/module/__init__.py
```

---

## 4. After Editing Code

1. **Run tests** — verify changes don't break existing functionality
2. **Check imports** — ensure new dependencies are added to requirements
3. **Update exports** — modify `__init__.py` if adding public classes
4. **Update docs** — keep README and docstrings in sync

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_module.py -v

# Check for import errors
python -c "from src import *"
```

---

## 5. File Operations

### Creating New Modules
1. Create the `.py` file with proper docstring header
2. Add exports to parent `__init__.py`
3. Create corresponding test file in `tests/unit/`
4. Add imports to main module if needed

### Removing Modules
1. Search for all imports/usages first
2. Update all `__init__.py` files
3. Remove or update related tests
4. Check main.py and entry points

### Renaming/Moving
1. Find all references with grep
2. Update all imports
3. Update `__init__.py` exports
4. Update tests
5. Consider adding deprecation warning if public API

---

## 6. Testing Guidelines

### Test Structure
```
tests/
├── conftest.py       # Shared fixtures
├── unit/             # Fast, isolated tests
├── integration/      # Tests with real dependencies
└── fixtures/         # Test data files
```

### Writing Tests
- One test class per module being tested
- Use descriptive test names: `test_<function>_<scenario>_<expected>`
- Use fixtures from `conftest.py` for common setup
- Mock external services (HTTP, filesystem, etc.)

### Running Tests
```bash
pytest                           # All tests
pytest tests/unit/               # Unit tests only
pytest -k "test_name"            # Specific test
pytest --tb=short                # Shorter tracebacks
pytest -v                        # Verbose output
```

---

## 7. Dependency Management

### Adding Dependencies
1. Add to `requirements.txt` (runtime) or `requirements-dev.txt` (dev only)
2. Add to `pyproject.toml` under `[project.dependencies]`
3. Use version constraints: `package>=1.0.0,<2.0.0`

### Checking Dependencies
```bash
cat requirements.txt
cat pyproject.toml | grep -A 50 "dependencies"
pip list
```

---

## 8. Localization (i18n)

If the project has a `locales/` directory:

1. **All locale files** must have the same keys
2. **Base locale** is typically `en.json`
3. **Adding new strings**: Add to ALL locale files
4. **Check consistency**:
   ```bash
   # Compare keys across locales
   python -c "import json; keys = [set(json.load(open(f'locales/{l}.json')).keys()) for l in ['en','ru','es']]; print(keys[0] - keys[1])"
   ```

---

## 9. Common Patterns

### Async Code
```python
async def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

### Pydantic Models
```python
from pydantic import BaseModel, Field

class Config(BaseModel):
    """Configuration model."""
    name: str = Field(..., description="Name of the item")
    count: int = Field(default=0, ge=0)
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Processing %s items", count)
```

---

## 10. Troubleshooting

### Import Errors
```bash
# Check what's exported
python -c "import src; print(dir(src))"

# Find circular imports
python -c "from src.module import Class" 2>&1 | head
```

### Test Failures
```bash
# Run with full output
pytest tests/unit/test_file.py -v --tb=long

# Run single test
pytest tests/unit/test_file.py::TestClass::test_method -v
```

### Missing Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## 11. Quick Reference

| Task | Command |
|------|---------|
| Run all tests | `pytest` |
| Run with coverage | `pytest --cov=src` |
| Format code | `black src/ tests/` |
| Sort imports | `isort src/ tests/` |
| Lint code | `ruff check src/` |
| Type check | `mypy src/` |
| Install deps | `pip install -r requirements.txt` |
| Install dev deps | `pip install -r requirements-dev.txt` |

---

## 12. Rules Summary

1. **Discover before assuming** — always check current structure
2. **English only** — all code, comments, docstrings, commits
3. **Type everything** — public functions need type hints
4. **Test everything** — new code needs new tests
5. **Update exports** — keep `__init__.py` in sync
6. **Run tests** — verify after every change
7. **Document changes** — update README/CHANGELOG when needed
