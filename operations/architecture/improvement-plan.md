# GRACy — Combined Improvement Plan

**Date:** 2026-07-09 · **Status:** backlog filed as GitHub issues #2–#17 (see `../delivery/backlog.md`) ·
**Basis:** merged from two reviews —
the correctness/hygiene pass (impact × risk) and the depth pass (seams, deletion test,
`operations/archive/initial_review.md`). All figures verified against source.

Ranked most-actionable first: high impact, low risk, unblocks the rest. "Source" = which
lens surfaced it (impact review / depth review / both).

| # | Item | Impact | Risk | Source |
|---|---|---|---|---|
| 1 | End-to-end smoke test on `testDataset/` + CI | High | Low | impact |
| 2 | Command-runner module `run(tool, *args)` (path + return-code check + logging) | High | Low–Med | both |
| 3 | Delete the dead non-Qt twins (+ `.bak`, `._` copies) | Med | Low | both |
| 4 | Repo hygiene — un-track Miniconda installers/junk; fix `.gitignore` | Med | Low | impact |
| 5 | Alignment module `align(reads, ref) → bam` | Med–High | Med | depth |
| 6 | Extract a headless pipeline module (move the GUI↔pipeline seam) | High | Med–High | both |
| 7 | Fix committed `GRACy.py` artifact + hardcoded HPC path | Med | Low–Med | impact |
| 8 | Config module — keyed, validated parsing | Med | Med | both |
| 9 | `os.system` → `subprocess.run([...], shell=False)` (injection safety) | Low–Med* | High | impact |
| 10 | Collapse the Python 2 env (RAGOUT on Py3) | Med | Med | impact |
| 11 | Polish — `>null`→`/dev/null` (201×), typos, fork README | Low | Low–Med | impact |

\* Item 9 impact is low in a trusted lab; high if ever distributed.

## The one reframe
The headline risk is not security — it is **silent wrong science**. ~605 inline
`os.system(installationDirectory+"src/conda/bin/…")` calls discard their return codes, so a
failed alignment/assembler step continues silently and yields plausible-but-wrong output.
That is why item 2 (return-code checking) outranks item 9 (injection safety).

## Item detail

1. **Smoke test + CI.** `testDataset/` ships 4 input FASTQs but **no golden output** — so
   step one is a smoke + sanity run (pipeline completes; genome non-empty and plausible),
   then pin a known-good result as a **golden file** for real regression power. Wire to CI.
   The safety net that makes 2–10 safe.
2. **Command-runner module.** One deep module resolving the conda tool path, running the
   tool, checking the return code, and logging. Leverage: ~605 call sites, one interface.
   Merges the impact review's "return-code wrapper" with the depth review's #1 deepening.
3. **Delete dead twins.** Every live `*Qt.py` has a stale non-Qt twin (`assembly.py`,
   `genotyping.py`, `snpCalling.py`, `annotation.py`) — verified unreferenced in code **and**
   in `install.sh` — plus `.bak`/`._` copies. **Keep `src/.GRACy_main.py`** (install.sh builds
   the launcher from it). Soft precondition for 2/5/8 having one home.
4. **Repo hygiene.** `.git` is 332 MB — Miniconda installers (~117 MB), old `webin-cli` jars,
   `.DS_Store`/`._*` all tracked; `.gitignore` only excludes conda dirs. Delete from the
   working tree, extend `.gitignore`, download Miniconda at install. History purge to reclaim
   the 332 MB is a separate, higher-risk force-push — optional.
5. **Alignment module.** The bowtie2/bwa build→align→view→sort→index chain is one behaviour
   re-typed at ~28 sites (97 samtools calls across 11 files). `bowtiePE`/`bwaPE` proved the
   small interface but never left assembly. Promote to a shared module returning a sorted BAM;
   sits on top of the runner (2).
6. **Headless pipeline module.** Pipeline logic is a side-effect blob inside
   `Ui_Form.performAssembly` — no return values, state via `os.chdir` + files + the log widget,
   so the test surface *is* the Qt widget. Extract `assemble(config, log=cb) → result`; the GUI
   becomes a thin adapter. Enables HPC batch + CI. Largest item — attempt only after 1 and 2.
7. **`GRACy.py` artifact.** It is a build artifact `install.sh` regenerates, yet the committed
   copy bakes in `/home3/scc20x/…` (lines 1–2) — a fresh clone is broken until install runs.
   Gitignore + generate at install, or template cleanly. Cheap; blocks nothing.
8. **Config module.** `assembly.conf` is parsed positionally (`readline().split("\t")[1]`),
   schema-less and copy-pasted; a reordered/missing line silently shifts every field. Parse to
   a typed, validated object shared across modules; fail loudly at load. Pairs with `assemble(config)`.
9. **subprocess conversion.** User-supplied args concatenated raw into shell strings. **428 of
   the 858 `os.system` calls (~half) rely on shell features** (pipes, redirects, `&`, `cd`,
   globs), so a blind `shell=False` rewrite breaks them — incremental only, behind the test net.
   Once the runner exists, this is changing one module's implementation.
10. **Collapse the Python 2 env.** `install.sh` builds a second EOL Py2 env solely for RAGOUT.
    Move RAGOUT to Py3, single env. Scaffolding is science-sensitive — verify output unchanged
    under the smoke test before removing the old env.
11. **Polish.** 201 `>null` redirects write a literal file named `null` (not `/dev/null`); four
    log/UI typos; a two-sentence README for this fork.

## Recommended sequence
Dependencies matter more than the raw ranking:

- **Block one (this month): 1 → 2 → 3 → 4.** All high value, low risk; 1 makes everything after
  it safe. (3 is a *soft* precondition for 2 — delete dead copies first so you don't edit files
  that never run.)
- **Structural: 5 → 6 → 8**, behind the test net. **7** anytime.
- **Higher-risk modernisation: 9, 10** — ride on the runner and tests already being in place.
- **11** whenever.

A shareable HTML render of this plan (with the impact × risk matrix and dependency diagram) was
produced 2026-07-09; regenerate from this document if it drifts.
