# GRACy — what changed, and why it matters (2026-07-25)

**For:** the people who use GRACy to analyse genomes.
**Status:** delivered and merged. Automated test suite **41 tests, all passing**.
**Covers:** everything delivered since the last update you were sent
(`2026-07-23-install-toolchain-fix.md`, the fresh-clone install fix) — five pull requests plus the
testing groundwork that update left open.

---

## In one paragraph

The last release proved GRACy's ~25 bioinformatics tools would **install**. This release found that
installing them isn't the same as them **working** — three tools installed perfectly and then failed
the moment the pipeline tried to use them, and two of those failed *silently*, producing empty or
missing results while reporting success. All three are now fixed. As a result, **the assembly
pipeline has run from start to finish for the first time**, producing a complete HCMV genome.

---

## What was delivered

### The pipeline can now actually assemble a genome

The assembler, SPAdes, was pinned to a 2018 version that **crashes on any modern Linux system**. This
had been silently blocking the whole assembly stage. It's been upgraded to a current version, kept in
its own isolated environment so the rest of the toolchain stays exactly as it was.
*(PR #35, closes issue #30 — reasoning recorded in ADR-0002.)*

### Two silent failures fixed — the important ones

Silent failures are the dangerous kind: the software says it worked, and the output looks plausible,
but it's wrong. There's no way for you to tell.

- **Read normalisation was producing nothing.** A missing system library meant one tool couldn't
  start, so it quietly emitted zero reads and the assembly collapsed further down the line with an
  unrelated-looking error. *(PR #31)*
- **Variant calling was quietly doing nothing.** A packaging quirk meant one tool couldn't find Java
  on machines without it system-wide. It failed instantly, GRACy ignored the failure, and the pipeline
  carried on and applied an *empty* result. This affected **the assembly stage's consensus
  polishing as well as SNP calling** — not a corner of the app, the main path. *(PR #36, closes
  issue #33.)*

### A safety net so this class of problem is caught in future

The previous update ended with an open question: where should verification scripts, sample sets and
run outputs actually live? That's now settled and built, and it's what made the rest of this release
possible.

- A **permanent home for verification work** — reusable check scripts, known-good reference outputs,
  and throwaway run results kept separate from each other. *(commit `c9a8537`; layout documented in
  `tests/README.md`.)*
- A **reinstall reproducer** that rebuilds the entire toolchain from scratch, the way a clean install
  does. It reads its settings directly from `install.sh`, so it can't silently drift out of step with
  the real installer. This was the outstanding follow-up from the last update, and it's now the
  standing check for install problems. *(`tests/harness/verify_install.sh`.)*
- A **toolchain check** that verifies every tool GRACy relies on genuinely loads and runs on your
  machine, in seconds, without needing any data. This is what found the three failures above.
  *(PR #34 — run it with `bash tests/harness/verify_toolchain.sh`.)*
- An **end-to-end test** that drives the real pipeline on the bundled sample data and checks the
  output is a plausible genome. *(PR #32)*

Together these cover the three questions that matter: *does it install?*, *do the tools run?*, and
*does the pipeline produce a sensible genome?* Before this release only the first had an answer.

---

## How it was verified

We deliberately avoided the easy checks that would have looked green and told us nothing.

- **The whole pipeline was run end to end** on the sample dataset, through all six stages. It
  completed cleanly and produced a single, complete HCMV genome with **no ambiguous bases**. Two full
  runs produced genomes of 235,645 bp and 235,067 bp against a 235,646 bp reference — within about
  0.25%, which is normal run-to-run variation.
- **The Java fix was proved by reproducing the actual failure**, not a stand-in. An earlier successful
  run had been quietly propped up by a manual workaround in the test script; that was removed, and the
  pipeline was re-run on a machine with no system Java at all. The tool that used to fail instantly
  ran **seven times without a single error**.
- **Every tool was load-tested individually** — 33 tools confirmed to start and run.
- **The automated suite grew from 16 to 41 tests.** Each fix ships with a test that fails if the bug
  ever comes back, including one that runs the real tool under the exact conditions that broke it.

---

## What this means for you

- **Assembly works.** It previously could not complete at all on a current system.
- **Results you were getting may have been incomplete.** If you ran assembly or SNP calling on a
  machine without Java installed system-wide, the consensus-polishing and variant-calling steps were
  silently skipped. Those steps now run. This is the main reason to move to this version.
- **Problems will now be visible.** The failures fixed here were invisible; the checks added here are
  designed to make that class of problem announce itself instead.

**One thing to be aware of — this is a change from the last update.** That update could tell you "no
tool versions changed, so your results are unaffected." **This one can't.** The assembler upgrade
means assemblies produced now come from a modern version of SPAdes, and results may differ from
historical GRACy runs. It was unavoidable — the old version simply cannot run on current systems — but
if you're mid-study and comparing against earlier results, it's worth knowing.

---

## The two messages you saw during installation

You reported two sets of errors and asked whether they mattered. **Neither is a problem, and neither
is new.** Here's what each one is.

### "The environment is inconsistent" — the long list of packages

**Short answer: pre-existing, harmless, and already there in the previous release.**

We checked the logs from the *previous* release and found the identical warning appearing five times,
at the same two points in the install. So the theory you saw online — that it's a newer, chattier
message about something that was always there — is the correct one here. Nothing changed to cause it.

What's actually happening: GRACy keeps a small, separate **legacy Python 2 environment** purely for
four older tools (Ragout, mummer, bcftools, LoFreq). That environment is built from an installer
frozen in 2020, but the package repositories it downloads from have kept moving. A handful of 2025-era
packages therefore end up alongside 2020-era ones, and the package manager notices the mismatch.

Two things make it look far worse than it is:

1. When the package manager reports this, it lists the **entire environment** rather than just the few
   packages actually in conflict. That's why you're looking at ~57 lines. It is not 57 broken packages.
2. It's confined to that legacy environment. **The main GRACy environment is unaffected.**

We didn't just reason about it — we tested all five tools in that environment on a machine showing the
same warning. **All five load and run correctly.** The most plausible candidate for genuine breakage
(a Perl version clash affecting two alignment tools) turned out to work fine in practice.

### "WARNING: There was an error checking the latest version of pip"

**Short answer: cosmetic.**

This is `pip` trying to reach the internet to check whether a newer version of *itself* exists, and
failing — almost certainly outbound network restrictions on the HPC node. It happens *after* the
installation work is finished and has no bearing on what was installed.

### One real thing this did surface

While investigating, we found an unrelated genuine issue: one package in that legacy environment is
installed **without a version pin**, so different machines get different versions depending on the day
they installed. We observed exactly that — two installs days apart picked up different builds. It
isn't causing failures, but it undermines reproducibility. It's logged and will be fixed separately.

---

## Honest limits

- The **assembly** module has been exercised end to end. The other five modules (annotation,
  genotyping, read filtering, SNP calling, database submission) have not yet been run end to end —
  your testing will be the first real exercise of those.
- On a memory-constrained machine, one k-mer counting step can exhaust available RAM near the end of
  an assembly. We know the specific cause and the fix; it isn't yet part of the release. A normal HPC
  node has ample headroom.

---

## References

Everything below landed after the previous update (`2026-07-23-install-toolchain-fix.md`, PR #29).

| Change | Reference | Closes |
|---|---|---|
| SPAdes upgraded to a version that runs on modern Linux | PR #35 | #30 |
| Variant calling no longer silently skipped | PR #36 | #33 |
| Read normalisation no longer silently produces nothing | PR #31 | — |
| End-to-end pipeline test on sample data | PR #32 | — |
| Per-tool runnability check | PR #34 | — |
| Testing home + reinstall reproducer *(the last update's open follow-up)* | commit `c9a8537` | — |

Background: `operations/decisions/ADR-0002-spades-dedicated-env.md` (why SPAdes lives in its own
environment), `tests/README.md` (how the verification scripts are organised),
`operations/journal/2026-07-25.md` (session detail).
