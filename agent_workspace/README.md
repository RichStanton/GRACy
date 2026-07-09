# GRACy Code Improvement Project

## Goal

Shore up the GRACy codebase for stability, reliability, and maintainability. The primary risks today are silent pipeline failures (no error checking on external tool calls) and untestable code (all logic embedded in GUI constructors). This project works through those issues systematically, building a test harness as we go.

## Participants

| Initials | Name | Role |
|---|---|---|
| IK | Iain Keddie | Lead — architecture review, code review, implementation |
| RS | Richard Stanton | Reviewer — joins for phase 4 decisions |

## Current Status

**Phase 4 — IK/RS review and decisions** · Ready to begin (awaiting IK + RS session)

## Phases

| Phase | Description | Owner | Status |
|---|---|---|---|
| 1 | Architecture review — structural fundamentals | IK | Done |
| 2 | Code review — stability and best practices | IK | Done |
| 3 | Prioritised list of changes | IK | Done |
| 4 | Review decisions | IK + RS | **Ready to begin** |
| 5 | Implementation — changes + test harnesses | IK | Not Started |

## Key Documents

| Document | Location |
|---|---|
| Baseline architecture | `ARCHITECTURE.md` |
| Baseline code review | `initial_review.md` |
| Architecture review (phase 1) | `planning/architecture_review.md` |
| Code review (phase 2) | `planning/code_review.md` |
| Prioritised work plan (phase 3) | `planning/priority_plan.md` |
| Executive summary (handover) | `planning/executive_summary.md` |
| IK/RS decisions (phase 4) | `planning/decisions.md` |
| Task tracker | `tasks/TASKS.md` |
| Compounded learnings | `compound/` |
| Customer-ready Word documents | `output/` |

## Workflow — Compound Engineering

This project follows the Compound Engineering approach: 80% planning, 20% execution. Each phase should leave the next phase easier, not harder.

| Phase transition | CE step |
|---|---|
| Before starting a phase | `/ce-brainstorm` — clarify requirements and risks |
| Before implementing a task | `/ce-plan` — break into steps, identify unknowns |
| After implementation | `/ce-code-review` — systematic review before marking done |
| After each phase completes | `/ce-compound` — write learnings to `compound/<phase>.md` |
| Before treating a planning doc as authoritative | `/ce-doc-review` |

## For the Agent

At the start of every session:
1. Read this file for project context
2. Read `tasks/TASKS.md` for current work state
3. Read the most recent file in `sessions/` for what happened last time
4. Read any relevant files in `compound/` for accumulated learnings

At the end of every session:
1. Update `tasks/TASKS.md` — move completed items, update in-progress
2. Write a session log in `sessions/YYYY-MM-DD.md`
3. If a phase completed, write `compound/<phase>.md` with learnings
