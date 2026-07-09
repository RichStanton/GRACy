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

## Scope

These are targeted regression tests tied to specific fixes (each references its issue).
A full end-to-end smoke test on `testDataset/` with a golden output is tracked separately
in issue #11 — that is the pipeline-level safety net; these are unit-level guards.
