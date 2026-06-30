# Contributing a task

This repository accepts one kind of contribution: a single, original Harbor task
under `tasks/<slug>/`. You check the task yourself with `harbor` and `ruff`, then
open a draft pull request for review.

## Prerequisites

- Docker, running locally.
- The harbor CLI: `uv tool install harbor`.
- ruff and the GitHub CLI (`gh`), authenticated.
- An E2B account. Create one at e2b.dev and put the key in `.env` at the repo root:

  ```
  E2B_API_KEY=your-key-here
  ```

## Workflow

1. Fork and clone the repository.

2. Scaffold and branch:

   ```bash
   cp -r tasks/_template tasks/<slug>
   git checkout -b task/<slug>
   ```

   Open a draft PR titled `Add task: <slug>` once you have a commit to push.

3. Design the four parts of the task. Read `docs/TASK-SPEC.md`. The verifier should
   have at least 30 table-driven cases, including edge cases and one that would
   regress to the broken starter.

4. Check your task as you iterate (run these yourself):

   ```bash
   harbor run --path tasks/<slug> --agent oracle   # must reach reward 1
   harbor run --path tasks/<slug> --agent nop      # must reach reward 0
   ruff check tasks/<slug>
   ```

   Confirm your task.toml, Dockerfile, tests/, and instruction.md follow the
   contract in `docs/TASK-SPEC.md`.

5. Commit your work, then push the branch and open a draft PR:

   ```bash
   git add tasks/<slug> && git commit -m "Add task: <slug>"
   git push -u origin task/<slug>
   gh pr create --draft --title "Add task: <slug>" --body "Task submission for <slug>."
   ```

   In the PR description, include the task slug and category, a short summary of
   the bug or missing behavior, why the task is non-trivial, what common
   incorrect solution your verifier catches, and the local oracle, nop, and ruff
   results.

6. When oracle reaches reward `1`, nop reaches reward `0`, ruff is clean, and you
   are confident in the task quality, mark the PR ready for review (`gh pr ready`
   or the GitHub UI).

## What the grader runs

A grader checks out your PR branch and reproduces the objective gates:

```bash
harbor run --path tasks/<slug> --agent oracle
harbor run --path tasks/<slug> --agent nop
ruff check tasks/<slug>
```

The objective gate passes only when the oracle scores 1, the nop scores 0, ruff
is clean, and the task follows the static contract in `docs/TASK-SPEC.md`. The
rest is human review.
