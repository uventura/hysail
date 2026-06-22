# AGENTS.md

Guidance for agentic coding agents working in the HySail repository. HySail is a
Python package and CLI that encodes files into packets, distributes them across
storage servers, reconstructs them, and optionally publishes manifests on-chain.

## Build / Lint / Test

Prefer the Makefile targets when `make` is available; fall back to raw commands otherwise.

| Task | Command | Notes |
| --- | --- | --- |
| Build/install package | `./scripts/build.sh` | Always build with this script (editable install) |
| Prepare environment | `make environment` | Activates venv via `scripts/start.sh`, then builds |
| Format code | `make format` | Runs `ruff format .` then `black .` |
| Lint | `ruff check .` | Fix all ruff issues before committing |
| Run all tests | `make test` or `pytest` | pytest discovers `hysail/**/tests` |
| Run a single test file | `pytest hysail/utils/tests/padding_test.py` | |
| Run a single test | `pytest hysail/utils/tests/padding_test.py::test_when_padding_is_valid_then_remove_padding_returns_original_payload` | |
| Run tests matching keyword | `pytest -k padding` | Substring match on test names |
| End-to-end example | `make lorem_example` | Run to verify encode/decode flow still works |
| Build thesis | './scripts/build_thesis.sh' | Always run when Latex content is intended to be updated

- Python `>=3.10` is required.
- Pinned tools: `black==24.8.0`, `flake8==7.0.0`, `ruff==0.15.6`, `pytest==9.0.2`.
- There is no custom ruff/black config; defaults apply (black line length 88).
- On Windows without `make`: `pip install -e .`, `ruff format .`, `black .`, `pytest`.

## Project Layout

- `hysail/` — main package. Entry point CLI is `hysail/hysail.py` (`hysail` command).
- `hysail/encryption/` — encode/decode, blocks, MAC, metadata.
- `hysail/chain/` — on-chain publishing (web3, manifests).
- `hysail/server/` — server and packet storage abstractions.
- `hysail/utils/`, `hysail/logger/`, `hysail/audit/` — helpers.
- Tests live next to code in `tests/` subpackages (e.g. `hysail/utils/tests/`).
- `dapp/` — separate JS/TS DApp (Hardhat); not part of the Python test suite.

## Code Style

### Imports
- Order groups: standard library, then third-party, then local `hysail.*` imports,
  separated by blank lines.
- Use absolute imports rooted at `hysail` (e.g. `from hysail.encryption.block import Block`).
- Module aliases are used for util-heavy modules: `import hysail.utils.galois as ga`,
  `import hysail.utils.operators as op`.
- Import specific names rather than whole modules when only a few symbols are used.

### Formatting
- Formatted by both `ruff format` and `black` — always run `make format` before committing.
- 4-space indentation, double-quoted strings, trailing commas in multi-line collections.
- Keep multi-line function signatures and dict literals split one item per line
  (matches existing `click.option` and ABI definitions).

### Types
- Type hints are used in newer code (e.g. `chain/`): annotate function params and
  returns (`def publish_manifest(self, manifest: dict) -> dict:`).
- Use `list[int]`, `dict`, etc. (PEP 585 builtins, since Python 3.10+).
- Prefer `@dataclass` for simple data containers (see `LocalBlock` in `encryption/block.py`).
- CLI command functions (Click) typically omit annotations; follow surrounding style.

### Naming
- Modules and files: `snake_case` (test files use the `_test.py` suffix).
- Classes: `PascalCase` (`Encode`, `HysailChainPublisher`, `LocalMac`).
- Functions, methods, variables: `snake_case`.
- Private/internal methods and helpers prefixed with a single underscore
  (`_encode`, `_generate_packet`, `_create_progress`).
- Constants: `UPPER_SNAKE_CASE` (e.g. `POLYNOMIAL_SET_SIZE`, `FILE_REGISTRY_ABI`).
- Module-level CLI helpers prefixed with `_` (`_enable_debug_mode`).

### Comments & Docs
- DO NOT add comments unless explicitly requested; the codebase is largely
  comment-free. Let names carry meaning.
- No docstrings are required to match existing style; keep additions minimal.

### Error Handling
- Raise `ValueError` with a clear message for invalid input/state
  (e.g. `raise ValueError("Data cannot be empty")`).
- In CLI code, raise `click.ClickException(...)` for user-facing failures.
- Use f-strings for error messages including offending values.
- Validate inputs early at the top of constructors/functions (fail fast).

### Patterns & Conventions
- Use the `rich`-based progress helpers (`get_progress`, `create_progress_task`,
  `advance_progress`) for long-running loops; gate global state via `set_progress`.
- Use `pathlib.Path` for filesystem paths in newer code; always pass
  `encoding="utf-8"` to `open`/`read_text`/`write_text`.
- CLI is built with `click`: `@main.command(...)`, `@click.argument`, `@click.option`
  with `help`, `default`, and `show_default` where useful.
- Read secrets (e.g. signer keys) from env vars (`HYSAIL_CHAIN_PRIVATE_KEY`); never
  hardcode or commit private keys or credentials.

## Testing Conventions (from .github/copilot-instructions.md)

- Use `pytest`. Name tests `test_<functionality>_<expected_behavior>`, e.g.
  `test_when_padding_is_valid_then_remove_padding_returns_original_payload`.
- Place tests in a `tests/` subpackage next to the code, in `<name>_test.py` files.
- Keep tests focused with plain `assert` statements; no test class required.

## Pre-Commit Checklist (required)

1. Build with `./scripts/build.sh`.
2. Run `ruff check .` and fix all linting errors.
3. Run `make format` (ruff format + black) to format the code.
4. Run `make test` (or `pytest`) and ensure tests pass.
5. Run `make lorem_example` to confirm the example encode/decode flow works.
6. Never commit secrets, private keys, or `.env` files.
