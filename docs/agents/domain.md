# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the
codebase. **GRACy diverges from the mattpocock default layout** — decisions and domain knowledge
live under `operations/`, not `docs/adr/` or a root `CONTEXT.md`.

## Before exploring, read these

- **`operations/architecture/ARCHITECTURE.md`** — current understanding of the codebase, pipeline
  stages, and tool dependencies.
- **`operations/decisions/`** — ADRs, append-only. Read any that touch the area you're about to work in.
- **`operations/archive/initial_review.md`** — historical first-pass review, not maintained; background only.

This is a **single-context repo** — one architecture doc, one decisions folder, no per-module split.

## Use the domain's vocabulary

GRACy is a genome-analysis pipeline wrapper (HCMV/CMV bioinformatics). Prefer terms already used in
`operations/architecture/ARCHITECTURE.md` and the pipeline stage names (read QC, assembly,
genotyping, SNP calling, annotation, ENA submission) over inventing new ones.

## Flag ADR conflicts

If your output contradicts an existing ADR in `operations/decisions/`, surface it explicitly rather
than silently overriding it.
