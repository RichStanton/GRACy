# Issue tracker: GitHub

Issues and PRDs for this repo live as GitHub issues on **`RichStanton/GRACy`** (the `origin` remote —
this fork, not `upstream` `salvocamiolo/GRACy`). Use the `gh` CLI for all operations.

## Conventions

- **Create an issue**: `gh issue create --repo RichStanton/GRACy --title "..." --body "..."`. Use a heredoc for multi-line bodies.
- **Read an issue**: `gh issue view <number> --repo RichStanton/GRACy --comments`.
- **List issues**: `gh issue list --repo RichStanton/GRACy --state open --json number,title,body,labels,comments --jq '[.[] | {number, title, body, labels: [.labels[].name], comments: [.comments[].body]}]'` with appropriate `--label`/`--state` filters.
- **Comment on an issue**: `gh issue comment <number> --repo RichStanton/GRACy --body "..."`
- **Apply / remove labels**: `gh issue edit <number> --repo RichStanton/GRACy --add-label "..."` / `--remove-label "..."`
- **Close**: `gh issue close <number> --repo RichStanton/GRACy --comment "..."`

Always pass `--repo RichStanton/GRACy` explicitly — this clone has two remotes (`origin` = the fork
we work in, `upstream` = `salvocamiolo/GRACy`, the original project) and `gh`'s auto-detection can
pick the wrong one.

## When a skill says "publish to the issue tracker"

Create a GitHub issue on `RichStanton/GRACy`.

## When a skill says "fetch the relevant ticket"

Run `gh issue view <number> --repo RichStanton/GRACy --comments`.
