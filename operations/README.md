# operations/ — Agent Knowledge Base

Durable project knowledge for GRACy lives here — architecture notes, delivery method, and the
decision record. Code lives elsewhere (`src/`, `data/`); throwaway/legacy analysis lives in
`archive/`.

| Area | Folder | What it is |
|---|---|---|
| **Architecture** | `architecture/` | Current understanding of the codebase structure and pipeline. |
| **Delivery** | `delivery/` | How work flows — tracker, labels, PR/merge method, and the `backlog.md` index. |
| **Journal** | `journal/` | Dated progress log — what happened each working session. |
| **Decisions** | `decisions/` | ADRs — why, append-only. |
| **Archive** | `archive/` | Historical notes, not maintained (e.g. the original code review). |

## Conventions

- **All AI-authored knowledge goes under `operations/`.** Don't scatter analysis docs at the repo root.
- **Significant decisions become ADRs** in `decisions/`.
- **One fact, one home — link, don't restate.** `CLAUDE.md` points here; it doesn't copy content.
