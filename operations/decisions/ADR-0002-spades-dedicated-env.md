# ADR-0002 — Run SPAdes 4.x from a dedicated env (`src/condaSpades`)

- **Status:** accepted
- **Date:** 2026-07-24

## Context

The #11 smoke test proved the assembly pipeline could not complete end-to-end. After the khmer
`libgomp` fix (#31), assembly reached SPAdes, where the pinned **`spades=3.12`** (a 2018 build)
**segfaults** — `spades-core` and `spades-hammer` both SIGSEGV, even on SPAdes's own `--test`
toy dataset, with no missing libraries (`ldd` clean) and regardless of stack/thread limits. The
host runs **glibc 2.39**; SPAdes 3.12 was built against glibc ~2.27 (Ubuntu 18.04-era). A 2018
C++ binary crashing on a 2024 glibc is a runtime-ABI incompatibility, not a data or config bug
(filed as #30). This blocked the #11 golden and, with it, end-to-end verification of the
structural refactors (#12–#17).

A modern SPAdes (**4.2.0**) runs correctly on this box (`--test` → `TEST PASSED CORRECTLY`), and
still accepts the flags the pipeline uses (`--cov-cutoff`, `--careful`). So the fix is to upgrade
SPAdes. The complication: `spades=4.2.0` pulls in **Python 3.14**, which — if installed into the
py37 base env — would drag the interpreter off 3.7 and make the pinned base tools
(pyqt=5.9.2, biopython=1.76, bowtie2=2.3.5.1, …) unsolvable, exactly the failure [ADR-0001](ADR-0001-pin-miniconda3-py37.md)
guards against.

## Decision

Install SPAdes into its **own conda env, `src/condaSpades`** (SPAdes 4.2.0, with whatever Python
that build requires), leaving the py37 base env untouched. This mirrors the existing pattern of
`src/conda2` (a separate env for ragout/bcftools). The two call sites invoke it directly:

- `src/scripts/assembly/utils/getBestAssembly.py`
- `src/scripts/assembly/utils/createCenterScaffold.py`

both changed from `src/conda/bin/python src/conda/bin/spades.py …` to
`src/condaSpades/bin/python src/condaSpades/bin/spades.py …`. `install.sh` creates the env
(`conda create -p ./src/condaSpades … spades=4.2.0`) instead of installing `spades=3.12` into the
base. `src/condaSpades/` is gitignored like the other envs.

## Why

- **It runs.** SPAdes 4.2.0 completes on modern glibc where 3.12 segfaults — the whole point.
- **No cascade.** A separate env keeps SPAdes's Python-3.14 requirement away from the py37 base,
  so ADR-0001's pins stay intact. Same isolation strategy already used for `src/conda2`.
- **Minimal code churn.** The pipeline's SPAdes command line is unchanged (`--careful`,
  `--cov-cutoff auto`, `-k …` all still valid in 4.x); only the interpreter/script paths move.

## Consequences / trade-offs

- **The assembly result is a *modern-SPAdes* result.** SPAdes 4.x is a different assembler build
  from 3.12; assembled genomes may differ. Any #11 golden blessed now is the baseline for the
  **upgraded** pipeline, not the original 2018 one. That is an accepted deliberate change, not a
  regression — the pinned 3.12 does not run on current systems at all.
- **Two Python worlds in one repo** (py37 base + condaSpades). Acceptable; `src/conda2` already
  established the precedent.
- **Scope:** only the de-novo assembly SPAdes calls moved. Nothing else in the pipeline changed.
  The broader toolchain modernisation (revisiting the other EOL pins) remains open future work.

## Related

- #30 (SPAdes 3.12 segfault — this ADR is its "upgrade" resolution)
- #11 (smoke test — this unblocks blessing its golden)
- ADR-0001 (why the base env stays on py37)
