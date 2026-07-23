# ADR-0001 — Pin the Miniconda3 installer to a Python-3.7 build

- **Status:** accepted
- **Date:** 2026-07-23

## Context

`install.sh` bootstraps the toolchain by downloading Miniconda3 and installing ~25
version-pinned bioinformatics packages into its base env. The #7/#8 repo-hygiene batch removed
the bundled installer and switched to downloading `Miniconda3-latest-Linux-x86_64.sh`. "Latest"
is a moving target, and on a fresh clone (user feedback, 2026-07-23) it broke the install two
ways at once:

1. **Terms-of-Service gate.** Current conda refuses to install from Anaconda's default channels
   until their ToS is accepted, aborting every unattended `conda install` with
   `CondaToSNonInteractiveError`. (Blocked the entire first install run.)
2. **Python 3.14 base.** "Latest" now ships Python 3.14, which conda pins into the base env. The
   pinned tools (bowtie2=2.3.5.1, cutadapt=2.6, bwa, blast, biopython, pyqt, …) require Python
   3.6/3.7 and become unsolvable. (11 packages still failed after the ToS gate was bypassed.)

The pinned tool versions are load-bearing for reproducible scientific results, so changing them
to chase a modern Python was not acceptable as a bugfix.

## Decision

Pin the Miniconda3 download in `install.sh` to **`Miniconda3-py37_23.1.0-1-Linux-x86_64.sh`**
(conda 23.1.0, Python 3.7). Do not use `-latest`.

## Why

- conda 23.1.0 **predates the ToS gate**, so unattended installs from the default channels
  proceed — fixing failure (1) without scripting `conda tos accept` (which the pinned conda
  wouldn't even recognise).
- Its **Python 3.7 base** is what the pinned tools were resolved against, fixing failure (2)
  with **zero change to any tool version** — so pipeline results are unaffected.
- This is the exact build the known-good dev environment (`src/conda`) was created from.
- Alternatives rejected: (a) keep `-latest` + `conda tos accept` + a dedicated py37 env —
  larger change, rewrites every `src/conda/bin/...` path reference, still fights the modern
  solver; (b) keep `-latest` + modernise all tool versions — changes scientific tool versions,
  needs full revalidation, out of scope for a regression fix. Both deferred to a future
  modernisation effort if desired.

## Consequences

- The toolchain stays on an **EOL Python 3.7 / old conda** by design. A future "just upgrade
  Miniconda" change would reintroduce the break — guarded by an in-script `WHY` comment and a
  regression test (`tests/test_install_miniconda_pin.py`) that fails if the download is
  repointed at `-latest` or any non-py37 build.
- Verified by a full 25-tool sequential reinstall from the pinned installer: **30/30 packages
  installed, 0 failures, 0 ToS gates**; matches the known-good baseline.
- A genuine modernisation (current Python + current tool builds, revalidated) remains open as
  separate future work, and would supersede this ADR.
- Delivered in [PR #29](https://github.com/RichStanton/GRACy/pull/29); see the executive summary
  in `../delivery/2026-07-23-install-toolchain-fix.md`.
