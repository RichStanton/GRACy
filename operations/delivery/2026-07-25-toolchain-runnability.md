# GRACy — "installed" made "runnable" (2026-07-25)

**For:** the maintainer / anyone testing this build.
**Status:** four pull requests — **#31, #32, #34, #35 — all open, none merged** (no self-merge; merges
are yours). Test suite **30/30 green** with #32 and #35 applied; #31 and #34 add their own guards on top.

> **Read this first — unlike every previous batch, this one *can* change analysis results.** PR #35
> upgrades SPAdes from 3.12 (2018) to 4.2.0. Assemblies produced after this batch are modern-SPAdes
> assemblies. See *Scientific impact* below. Everything else here is packaging and test scaffolding
> with no effect on output.

**TL;DR:** The previous batch proved the toolchain **installs**. This one found that installing isn't
the same as **running** — three tools installed cleanly and then failed at run time, two of them
*silently*. Two are now fixed, one is filed for you. The headline result: with the SPAdes fix in
place, **the assembly pipeline completed end to end for the first time**, producing a 235,645 bp HCMV
genome against a 235,646 bp reference — though that run needed a manual workaround for the third
issue, so it is not yet proof the app is self-contained. See *What the fix unblocked*.

## The problem this batch addresses

`install.sh` reports success when a package *appears in `conda list`*. That check can't see whether the
binary actually loads. Building the #11 smoke test surfaced three tools that passed the install check
and then failed when the pipeline invoked them:

| Tool | What actually happened | Status |
|---|---|---|
| **khmer** | `ImportError: libgomp.so.1` → read normalisation silently produced **0 reads** → assembly aborted downstream | **Fixed** (PR #31) |
| **SPAdes 3.12** | `spades-core` and `spades-hammer` **segfault** on modern glibc — even on SPAdes's own toy test data | **Fixed** (PR #35) |
| **varscan** | Wrapper execs bare `java`, which isn't on `PATH` → exits 127, `os.system` discards the code → **4 consensus sites in *assembly*, plus SNP calling, silently do nothing** | **Open — [issue #33]** |

Two of these three failed *quietly*. That's the recurring risk in this codebase: stages that produce
wrong-but-plausible output rather than stopping.

## The changes

### PR #35 — SPAdes 4.2.0 in its own environment *(the one with scientific impact)*
- **What:** the pinned `spades=3.12` is a 2018 binary that segfaults on current glibc, which blocked
  assembly entirely. Upgraded to **SPAdes 4.2.0**, installed into a **separate environment**
  (`src/condaSpades`) rather than the main one.
- **Why separate:** SPAdes 4.x needs Python 3.14; the main environment is pinned to Python 3.7 for the
  other tools (pyqt, biopython, …). Putting 4.x in the shared environment would break them. This
  mirrors the existing `src/conda2` pattern. Recorded as **ADR-0002**.
- **Command line unchanged** — 4.x still accepts `--careful` and `--cov-cutoff auto`; only the
  interpreter path moves.
- **Test:** `bash install.sh`, then `src/condaSpades/bin/spades.py --version` → expect `v4.2.0`.

### PR #31 — khmer can load its library
- **What:** installs `libgomp` before khmer. Without it khmer couldn't import, and read normalisation
  emitted zero reads instead of failing — the assembly then died with an unrelated-looking error.
- **Test:** `bash install.sh`, then run **Assembly** with de novo normalisation enabled. Expect the
  normalisation step to report a non-zero read count.

### PR #32 — the #11 smoke test
- **What:** `tests/harness/smoke_assembly.{py,sh}` drives the **real** assembly pipeline on
  `testDataset/` and checks the output is a plausible genome. Plus a fast unit guard for the
  plausibility checks (suite 16 → 26 tests).
- **Caveat:** GRACy has no headless entry point — orchestration lives inside the Qt widget — so the
  harness drives the GUI **offscreen**. That coupling is exactly what **#14** removes; when #14 lands,
  this points at a real function instead.
- **The golden fingerprint is not yet blessed** — see below.

### PR #34 — a runnability sweep
- **What:** `tests/harness/verify_toolchain.sh`, companion to `verify_install.sh`. Load-checks every
  tool the pipeline shells out to and classifies failures (segfault / missing library / missing binary
  / broken wrapper). **33 tools ok**, plus the walls above. This is the instrument that found #30 and
  #33, and it's the fastest way to check a new machine.
- **Test:** `bash tests/harness/verify_toolchain.sh` — runs in seconds, needs no data or network.

## Scientific impact — read before merging #35

Every previous batch could honestly say "no change to analysis results". **This one can't.** Moving
from SPAdes 3.12 to 4.2.0 is a real change to the assembler: contigs, and therefore downstream
consensus and variant calls, may differ from historical GRACy runs.

The trade-off was deliberate: 3.12 **cannot run at all** on current systems, so the alternatives were
"upgrade" or "no assembly". If continuity with historical results matters for work in progress, that's
a decision for you, not a technicality — ADR-0002 records the reasoning.

Practically: any golden reference blessed from here on is the baseline for the **upgraded** pipeline,
not the 2018 one.

## What the fix unblocked — first complete end-to-end run

With #35 and #31 in place the assembly pipeline ran all six stages and produced a genome:

- **235,645 bp** in a single record, against the Merlin reference of **235,646 bp** — one base
  different.
- **Zero ambiguous bases** (no `N`s).
- Alignment rate **100%**; all six stage directories populated.

Previously the pipeline died at stage 2. This is the first time it has reached the end.

**Two caveats, and the first one matters.**

**The run was not representative of what a user gets.** The launcher script used for it
(`tests/_results/run_golden.sh`) contains `export PATH="$PWD/src/conda/bin:$PATH"` — a manual
workaround for **[#33]**. GRACy itself does not do this. Without that line, `src/conda/bin/varscan`
exits **127** (`java: command not found`), and because every call site uses `os.system(...)` — which
discards the exit code — the pipeline silently continues with an empty `output.vcf`. That affects
**four sites in the assembly module** (`assemblyQt.py` lines 532, 599, 666, 1005), not just SNP
calling.

So this end-to-end result was produced in a hand-patched environment. It demonstrates that **SPAdes
4.x unblocks the assembly**, which was the point of #35 — but it does **not** yet demonstrate that the
application is self-contained. That needs a re-run without the workaround, after #33 is fixed.

**The run also did not exit cleanly.** After writing the final genome, the closing variant-calling
pass was **`Killed`** — a SIGKILL from the out-of-memory killer, not a crash in GRACy. The dev box has
7 GB total / ~4 GB available, so this is very likely environmental rather than a defect; an HPC node
should not hit it. Worth confirming on the target machine. So:

- The genome **was** produced and looks correct.
- The harness never got to print a clean fingerprint, so **`tests/expected/smoke_assembly.fingerprint`
  is still empty and the golden is still unblessed.**
- The memory ceiling of the run environment is now itself a finding worth a look — it died on a small
  test dataset.

Treat "the pipeline works end to end" as **strongly evidenced but not yet locked in**. Blessing the
golden needs one clean run.

## Install warnings reported from the field — investigated, no action needed

A user reported two sets of messages from a fresh install. Both were checked:

- **"The environment is inconsistent"** (a ~57-package wall of text) — **pre-existing, not a
  regression.** The identical warning appears five times in the logs from the *previous* release, at
  the same two install steps. It's confined to the legacy Python 2 environment (`src/conda2`, kept only
  for Ragout/mummer/bcftools/LoFreq); the main environment is unaffected. All five tools in that
  environment were verified to load and run despite it. Conda lists the whole environment rather than
  just the conflict, which is why it looks worse than it is.
- **"error checking the latest version of pip"** — pip's self-update check failing to reach the
  network. Emitted after the install work is done; cosmetic.

**One genuine issue did surface from that investigation:** [`install.sh:403`](../../install.sh#L403)
installs `openblas` **unpinned**, so different machines get different builds depending on install date
— we observed 0.3.33 and 0.3.34 days apart. Not causing failures, but it's silent drift in exactly the
work where we're trying to establish a reproducible reference. Worth a small pin. Not in this batch.

## Still open after this batch

- **[#33] varscan / bare `java`** — **the blocker for user testing.** Silent no-op wherever there's no
  system java, including four consensus sites in the assembly module. Silent wrong output is the worst
  failure mode for a wet-lab user, who has no way to tell. The fix (put `src/conda[2]/bin` on `PATH` at
  startup) is small and also hardens every other tool call. Pairs naturally with **#12**.
- **The #11 golden** — needs one clean end-to-end run (see above), then
  `bash tests/harness/smoke_assembly.sh` → review the fingerprint → write
  `tests/expected/smoke_assembly.fingerprint` → re-run with `--golden`.
- **CI workflow** — written but unpushable: the `developer-keystrand` token lacks `workflow` scope. The
  YAML is in PR #32's body for you to commit with a suitably scoped token.
- **[#17] collapse the Python 2 environment** — this batch's investigation is decent supporting
  evidence for prioritising it; it removes the whole class of `conda2` inconsistency noise.
- Carried over: community **PR #22** is redundant and should be closed (third-party, yours to close);
  the exposed `developer-keystrand` PAT still needs rotating.

## Suggested merge order

`#31` (libgomp) → `#34` (sweep) → `#35` (SPAdes, **the decision point**) → `#32` (smoke harness, most
useful once the others are in). Nothing here is order-critical, but #32's value depends on the rest.
