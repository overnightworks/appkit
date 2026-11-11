# design

## Commands

- `pnpm run` lists the package scripts. design has no other task runner.
- `pnpm exec vitest run <file>`: one Vitest file of `src/lib`. Needs `pnpm install --frozen-lockfile`.
- `pnpm run check`: the Svelte and TypeScript type check. Needs `pnpm install --frozen-lockfile`.
- `uv run --frozen --extra catalogs pytest -q tests/<module>.py -k <behaviour>`: one Python module; `--extra catalogs` installs Babel for `tests/catalogs`. `tests/test_npm_package.py`, `tests/catalogs/test_typescript_type_check.py` and `tests/catalogs/test_python_module_type_check.py` need `pnpm install --frozen-lockfile` first. CI adds `--cov=design --cov-branch --cov-fail-under=100`.
- `uv run --frozen ruff check .` and `uv run --frozen ruff format --check .`: Python lint; both must pass.
- `quality check`: the shared static check. Run it at the release `.github/workflows/ci.yml` pins.
- `pnpm run test:consumer`: the Playwright consumers, a probe stack. Run it only under the `flock` rule in the global contract's section "Machine load and local runs".
- `gh workflow run release.yml -R overnightworks/design -f version=X.Y.Z`: the operator's release dispatch. `main` must carry X.Y.Z in `pyproject.toml` and `package.json`.

## Rules

- After the operator's release run, the head replaces GitHub's generated release notes, below the hashes, with the version's notes: what changed, the breaking changes and the upgrade steps.

## Owners

- The operator dispatches every release.

## Documents

- `README.md`: read when you need to use the kit or see how it is distributed and released.
- `docs/VISION.md`: read when you need to know what design is for and whom it serves.
- `docs/ARCHITECTURE.md`: read when you change the parts, the build or the release path.
- `docs/stylesheet.md`: read when writing markup against `design.css` or the components.
- `docs/languages.md`: read when you build or judge an app's languages, or the kit's words.
