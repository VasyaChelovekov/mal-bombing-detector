# Refactor Notes

## Executive summary
- Introduced a live, read-only `ConfigView` proxy and routed CLI + exporter option resolution through it to reduce drift while keeping the config schema intact.
- Standardized failure recording via `FailureRecord.from_exception` / `from_message` factories to preserve the JSON schema and timestamps across stages.
- Centralized export metadata/summary/failure aggregation in a shared helper without changing any output fields; JSON exporter now consumes it while keeping payload shape stable.
- Clarified CLI option precedence for `analyze`, `single`, and `compare`, and tightened output directory rules to avoid double `reports/` segments.
- Kept CLI surface, config schema, export schema, i18n, caching, and rate limiting behaviors stable; only intentional visible change is that `version` now prints the packaged `__version__` string.
- Added targeted tests for ConfigView resolution, exporter aggregation, failure factories, output path rules, and the version command to lock the behaviors in place.

## Compatibility and invariants
- CLI flags/options: unchanged; precedence clarified (CLI args win over config, then defaults). The `version` command output now reflects `src/_version.__version__` but the command name/flags are unchanged.
- Config schema: unchanged (still YAML-based, same keys). `ConfigView` is a proxy, not a copy, so updates to the global config are reflected live.
- Export schemas (including JSON): unchanged; aggregation helper preserves the existing metadata/summary/results/failures fields and counts.
- I18n/caching/rate limiting: untouched; existing language selection, cache toggles, and adaptive delay config stay as-is.

## Patch-by-patch change log (chronological)
- Patch 1 (P1-A) FailureRecord factories
  - Files: `src/core/models.py`, `tests/unit/test_failures.py`
  - Intent: unify failure construction while preserving schema and timestamps.
  - Key refactors: added `from_exception` and `from_message` helpers; ensured `to_dict` keeps stage/error/message/title/url/timestamp stable.
  - Tests: `tests/unit/test_failures.py` checks schema fidelity and timestamp presence.
  - Risks: relies on `datetime.now()`; deterministic enough for current tests.

- Patch 2 (P1-B) ConfigView proxy introduction
  - Files: `src/utils/config.py`, `tests/unit/test_config_view.py`
  - Intent: provide a read-only, live view over the global config to avoid accidental mutation and keep defaults consistent.
  - Key refactors: added frozen `ConfigView`, `get_config_view`; blocked attribute reassignment while exposing live values.
  - Tests: `tests/unit/test_config_view.py` validates proxy reflection of defaults and immutability enforcement.
  - Risks: call sites must hold the view, not snapshots, to see runtime config reloads.

- Patch 3 (P1-C) Analyze command precedence and output paths
  - Files: `src/cli/commands.py`, `tests/unit/test_cli_config_view.py`, `tests/unit/test_cli_analyze_paths.py`
  - Intent: enforce CLI > config > defaults for `analyze` and make output directory handling auditably deterministic.
  - Key refactors: `_resolve_analyze_options` uses ConfigView; `_ensure_reports_dir` appends a single `reports` segment when config output is a base; CLI `--output` treated as final path without suffixing.
  - Tests: Config precedence (`test_cli_config_view.py`) and path semantics (`test_cli_analyze_paths.py`) cover config bases, CLI overrides, and avoidance of double `reports/`.
  - Risks/edge cases: callers passing a path already ending with `reports` will not get an extra segment (by design).

- Patch 4 (P1-D) Single command precedence
  - Files: `src/cli/commands.py`, `tests/unit/test_cli_single_config.py`
  - Intent: align `single` with ConfigView semantics; keep language from config, allow CLI platform override.
  - Key refactors: `_resolve_single_options` uses ConfigView; language sourced from config, platform CLI > config.
  - Tests: `test_cli_single_config.py` covers config defaults and CLI platform override.
  - Risks: none noted; behavior preserved.

- Patch 5 (P1-E) Compare command precedence
  - Files: `src/cli/commands.py`, `tests/unit/test_cli_compare_config.py`
  - Intent: mirror ConfigView resolution for `compare` (language from config; platform CLI > config).
  - Key refactors: `_resolve_compare_options` parallels `single` semantics.
  - Tests: `test_cli_compare_config.py` validates defaults and CLI override.
  - Risks: none noted; behavior preserved.

- Patch 6 (P1-F) Exporter aggregation helper
  - Files: `src/exporters/aggregation.py`, `tests/unit/test_export_aggregation.py`
  - Intent: centralize metadata/summary/results/failures assembly without changing JSON schema.
  - Key refactors: added `build_metadata`, `build_summary`, `aggregate_failures`, `serialize_result`, and `build_export_payload` using accurate totals and stable ordering.
  - Tests: `test_export_aggregation.py` checks counts, level tallies, failure order, and payload shape.
  - Risks: currently only consumed by JSON; other exporters still bespoke (see Open items).

- Patch 7 (P1-G) JSON exporter ConfigView adoption
  - Files: `src/exporters/json_export.py`, `tests/unit/test_json_exporter.py`
  - Intent: let JSON exporter default to ConfigView export settings and reuse the aggregation helper while keeping output schema intact.
  - Key refactors: default `output_config` now `config_view.export`; export payload built via `build_export_payload`; still honors explicit `ExportConfig` overrides and pretty flag.
  - Tests: `test_json_exporter.py` verifies ConfigView defaulting, override behavior, metadata language/version, and payload integrity.
  - Risks: none observed; schema preserved.

- Patch 8 (P1-H) Version centralization
  - Files: `src/_version.py`, `src/cli/commands.py`
  - Intent: avoid heavy imports for version lookup and keep a single source of truth for version metadata.
  - Key refactors: added lightweight `_version` module; CLI `version` command prints `__version__`; aggregation helper reads `__version__` for metadata.
  - Tests: covered indirectly via exporter and aggregation metadata assertions.
  - Risks: requires bumping `src/_version.py` when releasing.

- Patch 9 (P1-I) Version command regression test
  - Files: `tests/unit/test_cli_version.py` (plus minor CLI wiring to import `__version__`).
  - Intent: lock the version command to the packaged `__version__` output.
  - Key refactors: CLI already wired to `_version`; added test to assert exit code 0 and version string presence.
  - Tests: `test_cli_version.py` via Typer `CliRunner`.
  - Risks: none; purely a guardrail.

## README update inputs (pasteable for docs refresh)
- CLI precedence rules
  - `analyze`: language/platform/format/output resolve as **CLI args > config file > built-in defaults**. If `--output` is omitted, config `export.output_directory` is used and suffixed with `reports` only if it does not already end with `reports`. `--format` defaults to config `export.default_format` when set, otherwise `excel,json`.
  - `single`: language always comes from config (`general.language`); platform resolves as **CLI `--platform` > config `platforms.default`**.
  - `compare`: language comes from config; platform resolves as **CLI `--platform` > config `platforms.default`**.
- Output directory semantics (reports folder rules)
  - When config `export.output_directory` is a base (e.g., `output`), the tool uses `<base>/reports` as the final directory.
  - When config `export.output_directory` already ends with `reports` (e.g., `output/reports`), it is used as-is with no extra suffix.
  - `--output` is interpreted as the **final directory** (no automatic `reports` suffix). Ex: `--output C:/tmp/run` yields files in `C:/tmp/run/top_{n}_analysis_*.{ext}`.
  - Config-driven example: `export.output_directory: output` → writes to `output/reports/top_{n}_analysis_*.{ext}`; `export.output_directory: output/reports` → writes to `output/reports/top_{n}_analysis_*.{ext}`.
- Version behavior
  - `__version__` lives in `src/_version.py`.
  - `python -m src version` now prints `MAL Bombing Detector v{__version__}` using that module.
- End-user visible behavior changes
  - `analyze` output path avoids double `reports` when config already ends with `reports`, and respects CLI `--output` as the exact target directory.
  - `version` command reflects the packaged `__version__` string (previously could drift).

## Technical details for maintainers
- Failure handling refactor: `FailureRecord.from_exception` and `from_message` encapsulate schema-safe construction used in analyzer failure paths and export aggregation; timestamps are assigned on creation.
- ConfigView semantics: acts as a live proxy (not a snapshot), blocking attribute reassignment. Adopted in CLI option resolution and JSON exporter defaulting; other modules still reading `get_config()` will not benefit until migrated.
- Exporter aggregation helper: centralizes metadata totals, level counts, metrics serialization, and failure flattening without schema changes; currently consumed by JSON exporter (others still bespoke).
- Version centralization: `_version.py` holds `__version__` to avoid importing heavier modules; referenced by CLI `version` command and export metadata builders.

## Verification commands
```bash
ruff format .
ruff check .
pytest -q
```
- Latest observed result: `pytest -q` → **73 passed** (Python 3.12.10, Windows) on this branch.

## Open items / deferred work
- Extend the aggregation helper to Excel/CSV/HTML exporters so all formats share identical metadata/summary/failure assembly.
- Migrate remaining exporters and runtime code paths from direct `Config` access to `ConfigView` for consistent precedence handling.
- Evaluate README/CLI docs refresh using the "README update inputs" above to capture precedence/output semantics.