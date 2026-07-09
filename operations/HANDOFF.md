# HANDOFF — resume in the WSL session

**Written:** 2026-07-09 by the Windows-side Claude session (`C:\dev\GRACy`).
**You are:** a fresh Claude session running natively in **WSL Ubuntu at `~/projects/GRACy`** — now the single working home. The Windows clone is being retired.

## Decision on record (user chose Option 1)
Standardise on the **Matt Pocock skills + `operations/` knowledge base** as the dev methodology.
The earlier **Compound Engineering + OpenSpec** effort in this clone is retired *as a process* — but
its **analysis content is superior and must be MERGED IN, not discarded** (see the critical finding).

## ⚠️ CRITICAL — merge these bug findings into `operations/architecture/improvement-plan.md`
The earlier WSL effort (`agent_workspace/planning/`) ran **Ruff + Bandit** and found concrete bugs our
Windows review MISSED. Fold them in at the **top** of the plan (highest impact, lowest risk — mostly
1-line fixes):

- **BUG-1 (Critical):** `toPlainText` missing `()` in 5 modules (`assemblyQt.py:143`,
  `genotypingQt.py:194`, `snpCallingQt.py:273`, `dbsubmissionQt.py:319`, `readsFilteringQt.py:302`) —
  the "no files selected" guard never fires → crash with no message.
- **BUG-2 (Critical):** `completeGenome.py:105` writes `firstPortion` where it should write
  `lastPortion` → **SILENT WRONG GENOME FASTA** (last segment overwritten with a copy of the first).
  This is a live instance of the "silent wrong science" risk we only theorised.
- **BUG-3 (High):** `genotypingQt.py:511` hardcodes `16` instead of `kmerLength` → silent wrong k-mer counts.
- Plus 2 more confirmed bugs — see `agent_workspace/planning/code_review.md` (Confirmed Bugs).
- **Ruff:** 436 violations, **210 auto-fixable** (E712/E713), **68 undefined-names (F821)** — check for real bugs.
- **Bandit:** **916** `os.system` sites, **579** definite injection (B605), 167 partial-path (B607).
  Reconcile our plan's os.system counts to these authoritative numbers.
- Structural insights ours lacked: **13 `os.chdir()`** calls must be fixed during God-method extraction;
  **document inter-module contracts** (hardcoded dir names / magic filename suffixes) *before* refactoring;
  Class-B utils (`scaffold_builder.py`, `revComp.py`, `varscanFilter.py`) are subprocess stepping-stones.

Full detail: `agent_workspace/planning/{priority_plan.md, code_review.md, architecture_review.md,
decisions.md}` and polished `.docx` versions in `agent_workspace/output/`.

## Our plan (from the Windows side, now in `operations/`)
`operations/architecture/improvement-plan.md` — the 11-item impact×risk+depth plan (+ shareable
`improvement-plan.html`). Structurally sound (command-runner, alignment module, headless extraction,
config module, dead-code delete, repo hygiene, py2 collapse, subprocess) but **needs the bugs above
merged in as new top priorities**.

## Setup already done in THIS clone
- Matt Pocock skills installed at `.claude/skills/` (13 skills).
- `CLAUDE.md` replaced with the Matt Pocock version; old one preserved as **`CLAUDE.compound-eng.md`**
  (keep — it has the useful Ruff/Bandit run commands).
- `docs/agents/` installed (tracker = GitHub `RichStanton/GRACy`; triage-labels; domain).
- `operations/` knowledge base copied in (this file lives there).
- **compound-engineering plugin DISABLED** in `.claude/settings.json` (original:
  `.claude/settings.json.compound-eng.bak`).
- GitHub Issues enabled on `RichStanton/GRACy` with the 5 triage labels.

## Salvage / preserve — do NOT delete
- **`README.md`** — the good 94-line README (also backed up as `README.fuller-draft.md`). The canonical
  repo README is a 1-liner; replace it with this.
- **`pyproject.toml`** (Ruff) + **`.bandit`** — keep as active tooling.
- `agent_workspace/` (analysis + `.docx`), `archive/code_analysis/` — keep as reference.
  (`openspec/` was removed 2026-07-09 — the team is standardising on the Matt Pocock skills, not OpenSpec.)

## Git state — needs proper consolidation
- **This WSL clone:** base `e8ebff6`, with heavy **CRLF↔LF line-ending noise** across ~256 tracked
  files (cosmetic) + the untracked extras above. The copied Matt Pocock files are currently untracked here.
- **Windows clone `C:\dev\GRACy`:** HEAD `c336df5` (skills + operations + plan), clean, **not pushed**
  (origin/master is at `04b099c`).
- Consolidation:
  1. Stop the noise: `git config core.autocrlf false` and add `.gitattributes` (`* text=auto eol=lf`).
  2. Get onto `c336df5`: push it from Windows then fetch here, **or** commit the copied files directly.
     Preserve `README.md` (good one) + all untracked extras. Before any `git reset --hard`, back up
     `README.md` (already done → `README.fuller-draft.md`).
  3. Commit the merged plan + salvaged tooling.

## Environment
- WSL2 Ubuntu 24.04 (disk `F:\WSL\ext4.vhdx`, 266 GB free). GUI works via WSLg.
- **Toolchain NOT installed.** To run/test: `bash install.sh` (bundled Miniconda + ~25 bioconda tools;
  several GB, slow), then `./GRACy.py`. The Tier-1 bug fixes can be *edited* without the toolchain;
  only *running/testing* needs it.
- `gh` authed as `developer-keystrand` (push to `RichStanton/GRACy`, not admin).

## Suggested next steps (in order)
1. Confirm Matt Pocock skills loaded (`/grill-me`, `/to-prd`, `/to-issues`, `/triage`, `/tdd`, …).
2. Consolidate git so this clone is the clean single home.
3. Merge the WSL bug findings into `operations/architecture/improvement-plan.md` (bugs at top).
4. Salvage README (replace the 1-liner); confirm `pyproject.toml` / `.bandit` kept.
5. Run `install.sh` to get the toolchain; then build the smoke test and run GRACy.
6. Execute: the Tier-1 one-line bug fixes (BUG-1/2/3) first — highest value, lowest risk.
