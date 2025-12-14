# AI Assistant Instructions

## CONTEXT
- Repository: GitHub-hosted project
- Language: Python 3.10+
- Shell: PowerShell (Windows) or Bash (Linux/macOS)
- All code, comments, docstrings, commits: English only

## DISCOVERY PROTOCOL
Execute before any modification:
```
1. Read pyproject.toml → get dependencies, entry points, project metadata
2. Read src/__init__.py → get public exports
3. List src/ structure → understand module organization
4. Read tests/conftest.py → get test fixtures
5. Check config/ → find configuration files
6. Run: git status → check current branch and changes
7. Run: git log --oneline -5 → understand recent history
```

## CODE STANDARDS
```yaml
typing: required for all public functions
docstrings: Google-style (Args, Returns, Raises)
imports: stdlib | third-party | local (blank lines between)
naming:
  functions: snake_case
  classes: PascalCase
  constants: UPPER_CASE
max_function_lines: 50
prefer: composition over inheritance
models: Pydantic or dataclasses
```

## FILE OPERATIONS

### Create Module
```
1. Create src/{module}.py with docstring header
2. Add to src/__init__.py exports
3. Create tests/unit/test_{module}.py
4. Run pytest tests/unit/test_{module}.py
```

### Modify Module
```
1. Read target file completely
2. Search: grep -rn "ClassName\|function_name" src/ tests/
3. Check __init__.py for exports
4. Make changes
5. Run pytest
6. Update CHANGELOG.md if public API changed
```

### Delete Module
```
1. Search all usages: grep -rn "module_name" .
2. Remove imports from all files
3. Update __init__.py exports
4. Remove/update related tests
5. Run pytest
```

## TESTING PROTOCOL
```bash
pytest                              # All tests
pytest tests/unit/                  # Unit only
pytest tests/integration/           # Integration only
pytest -k "test_name"               # Specific test
pytest --tb=short                   # Short traceback
python -c "from src import *"       # Verify imports
```

## DEPENDENCY MANAGEMENT
```
Add runtime: requirements.txt + pyproject.toml[dependencies]
Add dev-only: requirements-dev.txt + pyproject.toml[dev-dependencies]
Format: package>=1.0.0,<2.0.0
After adding: pip install -r requirements.txt
```

## LOCALIZATION (i18n)
```
Location: locales/*.json
Base: en.json
Rule: ALL locale files must have identical keys
Verify: Compare key sets across all JSON files
When adding string: Add to ALL locale files simultaneously
```

## GIT WORKFLOW

### Before Starting Work
```bash
git fetch origin
git status
git branch -a                       # List all branches
git log --oneline -10               # Recent commits
```

### Feature Development
```bash
git checkout -b feature/{name}      # Create feature branch
# ... make changes ...
git add .
git commit -m "feat: description"   # Conventional commits
git push -u origin feature/{name}
# Create PR via GitHub
```

### Commit Message Format
```
feat: add new feature
fix: fix bug description
docs: update documentation
refactor: code refactoring
test: add/update tests
chore: maintenance tasks
```

### Sync with Main
```bash
git checkout main
git pull origin main
git checkout feature/{name}
git rebase main                     # Or: git merge main
```

### Pull Request Checklist
```
[ ] All tests pass: pytest
[ ] No lint errors: ruff check src/
[ ] Types valid: mypy src/
[ ] Imports clean: python -c "from src import *"
[ ] CHANGELOG updated (if public API)
[ ] Commit messages follow convention
```

## GITHUB ACTIONS
```
Location: .github/workflows/
Triggers: push to main, pull requests
Tests run: Python 3.10, 3.11, 3.12, 3.13
Check status: gh run list --limit 5
View logs: gh run view {run-id}
```

## GITHUB CLI COMMANDS
```bash
gh repo view                        # Repo info
gh pr list                          # List PRs
gh pr create                        # Create PR
gh pr checkout {number}             # Checkout PR locally
gh issue list                       # List issues
gh issue create                     # Create issue
gh run list                         # CI/CD runs
gh run watch                        # Watch current run
```

## ERROR RESOLUTION

### Import Errors
```bash
python -c "import src; print(dir(src))"
python -c "from src.module import Class"
```

### Test Failures
```bash
pytest tests/path/test_file.py -v --tb=long
pytest tests/path/test_file.py::TestClass::test_method -v
```

### Merge Conflicts
```bash
git status                          # See conflicted files
# Edit files, resolve <<<< ==== >>>> markers
git add {resolved_files}
git rebase --continue               # Or: git commit
```

### CI Failures
```bash
gh run list --limit 5
gh run view {run-id} --log-failed
```

## QUICK COMMANDS
```
| Task              | Command                           |
|-------------------|-----------------------------------|
| Run tests         | pytest                            |
| Run with coverage | pytest --cov=src                  |
| Format code       | black src/ tests/                 |
| Sort imports      | isort src/ tests/                 |
| Lint              | ruff check src/                   |
| Type check        | mypy src/                         |
| Git status        | git status                        |
| Push changes      | git push                          |
| Create PR         | gh pr create                      |
| View CI status    | gh run list                       |
```

## RULES
```
1. DISCOVER before assuming — verify current state
2. ENGLISH only — code, comments, commits
3. TYPE all public functions
4. TEST all new code
5. UPDATE exports in __init__.py
6. RUN tests after changes
7. COMMIT with conventional messages
8. PUSH to feature branch, not main
9. CREATE PR for review
10. SYNC with main before merging
```
