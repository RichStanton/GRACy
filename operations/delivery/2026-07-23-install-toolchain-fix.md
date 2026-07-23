# GRACy — fresh-clone install failure, fixed (2026-07-23)

**For:** the maintainer / anyone who hit the failed `install.sh` on a fresh clone.
**Status:** on a branch, in a PR awaiting your review/merge (no self-merge). No tool versions
changed — this is a packaging fix, not a scientific one, so pipeline results are unaffected.

**TL;DR:** A recent repo cleanup made `install.sh` download the *newest* Miniconda instead of a
bundled copy. "Newest" quietly changed two things that broke the whole toolchain install. We
pinned the download back to a known-good version — a one-line change — and proved it by
reinstalling all 25 tools from scratch.

## Why the problem existed

The bioinformatics tools GRACy relies on (bowtie2, cutadapt, bwa, blast, samtools, …) are
installed by `install.sh` through Miniconda. Until recently the installer shipped a fixed,
known-good copy of Miniconda. The last cleanup batch removed that bundled copy and had the
script **download `Miniconda3-latest`** instead — sensible on the surface, but "latest" is a
moving target, and it had drifted in two ways that both landed on the user:

1. **A new legal gate.** Current Miniconda ships a conda new enough to refuse installing from
   Anaconda's default channels until its Terms of Service are accepted. In an unattended
   script that became a hard stop — every install aborted. *(The wave of `CondaToS…` errors in
   the first log.)*
2. **A newer Python underneath.** "Latest" now builds on **Python 3.14**, which conda locks
   into the environment. GRACy's tools are pinned to older versions that require **Python
   3.6/3.7**; with 3.14 locked in they can't be installed. *(Why, after `export
   CONDA_PLUGINS_AUTO_ACCEPT_TOS=true` cleared the legal gate, 11 packages still failed with
   version conflicts in the second log.)*

The two-step experience — TOS errors, then version conflicts once TOS was bypassed — was these
two stacked problems surfacing one after the other.

## What was done to fix it

Pinned the Miniconda download to a specific older build — **`Miniconda3-py37_23.1.0`** (Python
3.7). That single choice resolves **both** problems: it predates the Terms-of-Service gate, and
it provides the Python 3.7 base the tools were designed against.

- **One line changed** in `install.sh` (plus a matching `.gitignore` entry).
- **No tool versions touched** — every package installs at the same version as before.
- A **regression test** (`tests/test_install_miniconda_pin.py`) fails if the script is ever
  repointed at "latest," so this can't silently recur.
- A comment in the script explains *why* the pin exists, to stop a future "upgrade" from
  reintroducing the break.

## What was done to prove the fix worked

We avoided the easy, misleading check (install one package, see it work) and instead ran the
real thing:

- **Full end-to-end reinstall** — all ~25 tools installed from scratch, in the script's real
  order, into a single fresh environment built from the pinned installer: the same path a clean
  clone hits.
- **Result: 30/30 packages installed, 0 failures, 0 Terms-of-Service gates.** Every one of the
  11 packages that failed on the user's machine now installs.
- **Both failure modes checked directly:** no TOS prompt on any Anaconda-channel install; no
  Python-version conflicts.
- **Matched against a known-good reference** environment — identical versions to the previously
  working setup.
- Automated test suite passes (16/16).

**Bottom line:** fixed at the root cause, smallest possible change, no effect on analysis
results, demonstrated by a complete reinstall rather than a spot check.

## Follow-ups (not in this change)

- A central home for test scripts / datasets / outcomes (`tests/harness/`, `tests/expected/`,
  etc.) was proposed but **not yet decided** — deferred pending maintainer sign-off.
- The full-chain install reproducer used to verify this fix is the natural first inhabitant of
  that `tests/harness/` once the layout is agreed.
