# appkit - Agent Guidance

This file holds appkit's own facts on top of the global contract. `CLAUDE.md`
imports it.

## Targeted proof

- One Vitest file: `pnpm exec vitest run <file>`; type check: `pnpm run check`.
- One Python module: `uv run --frozen pytest -q tests/<module>.py -k <behaviour>`
  (no pytest-xdist here, so no worker setting).
  `tests/test_npm_package.py` needs `pnpm install --frozen-lockfile` first.
- Python lint, both must pass: `uv run --frozen ruff check .` and
  `uv run --frozen ruff format --check .`.
- `quality hygiene .` is the remaining static check.
- The Playwright consumers (`pnpm run test:consumer`) are a probe stack: run them
  only under the `flock` rule in the global contract's section "Machine load and
  local runs". CI's `checks` job runs them, and the full suites.

## Release

The operator runs `scripts/publish_release vX.Y.Z` himself; it tags `main` and
publishes the wheel and the npm tarball. The head opens one release item per
dependent.
