# tests/

Lightweight regression tests for GRACy, using the stdlib `unittest` framework (no extra
dependencies). Tests that touch PyQt5 need the bundled Python environment and skip
themselves otherwise.

## Run

```bash
# From the repo root, using the bundled interpreter (has PyQt5, Biopython, etc.)
src/conda/bin/python -m unittest discover -s tests -v
```

Plain `python3 -m unittest discover -s tests` also works, but PyQt5-dependent tests will
be skipped unless PyQt5 is importable.

## Layout — the home for scripts, sets, and outcomes

| Location | Holds | Tracked? |
|---|---|---|
| `tests/` | unittest regression tests, one per fix, each naming its issue in the docstring | yes |
| `tests/harness/` | reusable **verification scripts** too heavy for unittest (e.g. `verify_install.sh`, the full toolchain-install reproducer) | yes |
| `tests/fixtures/` | small committed **inputs** a test needs | yes |
| `tests/expected/` | **golden / known-good outputs** to diff against (home for the issue-#11 e2e baseline once blessed) | yes |
| `testDataset/` | pipeline sample reads for smoke runs — lives at the repo root, referenced by path in the app | yes |
| `tests/_results/` | **live run outcomes / artifacts** — throwaway | no (gitignored) |

Principle: **outcomes are ephemeral and gitignored; only golden baselines are committed.**
Heavy experiments (throwaway conda installs, pipeline runs) write under `tests/_results/`
or a mktemp dir — never into the repo's real `src/conda`.

## Scope

These are targeted regression tests tied to specific fixes (each references its issue).
Two kinds of check live here:

- **Unit-level guards** (`tests/test_*.py`) — fast, stdlib `unittest`. Many pipeline scripts
  can't be imported standalone, so those tests use AST/text analysis of the source instead.
- **Full-chain harnesses** (`tests/harness/*.sh`) — heavier, run manually, prove real
  end-to-end behaviour. `verify_install.sh` reinstalls the whole toolchain from the pinned
  Miniconda build and reports per-package pass/fail + Terms-of-Service gates (guards
  [ADR-0001](../operations/decisions/ADR-0001-pin-miniconda3-py37.md); pairs with the
  `test_install_miniconda_pin.py` unit guard).

A full end-to-end smoke test on `testDataset/` with a golden output is tracked separately
in issue #11 — that is the pipeline-level safety net; its baseline belongs in
`tests/expected/`.
