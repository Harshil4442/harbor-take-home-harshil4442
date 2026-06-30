# Harbor Take-Home Assessment

> Build a tiny exam for AI coding agents. One task, fully self-contained: a broken
> codebase, a clear instruction, an oracle that fixes it, and a held-back verifier
> that grades any agent's attempt. The task is real when the oracle scores reward
> `1` and the untouched starter scores `0`.

## Why this exists

Coding agents are only as trustworthy as the tasks we measure them on. A good task
is a small, honest experiment: it has exactly one correct behavior, it cannot be
gamed, and it tells you something real about whether an agent can do the work.
Writing one is harder than it looks, and that is the point.

You are not solving a puzzle we wrote. You are writing the puzzle, the answer key,
and the grader, and proving all three agree. Do that well and you have shown more
than coding skill: you have shown you can reason about correctness, edge cases, and
how to stop a clever agent from cheating its way to a green check.

## Use any coding agent you like

This is the fun part: **you are encouraged to use a coding agent to build your
task.** Claude Code, Cursor, Aider, Codex, Gemini CLI, Windsurf, whatever you reach
for. Use it to scaffold the starter code, draft the verifier, and iterate on the
oracle. There are no rules against AI help here; using an agent well is a skill we
want to see.

The meta is the whole point: you are using an agent to build a test for agents.
The catch is that the agent cannot hide a weak task from the grader. Run the
oracle, the nop, ruff, and the verifier yourself so a task only passes when it
genuinely works. Lean on your agent; just read and understand everything it
produces before you submit. If you cannot explain why a test exists, it does not
belong in your task.

## Read every aspect before you start

This README is the map, not the territory. The task passes only when it satisfies
the full contract, so read all of it first:

- `docs/TASK-SPEC.md` — the complete task contract: the four parts, the schema, and
  the conventions every task must follow.
- `docs/EVALUATION.md` — the grader's rubric and the exact PASS/FAIL criteria.
- `CONTRIBUTING.md` — the workflow, prerequisites, and PR steps end to end.
- `tasks/_template/` — the blank skeleton you copy from.

Do not skim. The most common way to fail this assessment is to miss a single line
of the spec.

## Built on Harbor

Every task here is a Harbor task. Harbor is the open framework that defines the
task format and runs the oracle, the nop, and any coding agent against your
verifier inside a sandbox.

- Install the CLI: `uv tool install harbor`
- Framework and task-format reference: https://github.com/laude-institute/harbor

It is worth understanding how Harbor stages a run before you write a line: it
copies `environment/` into `/app`, runs the agent session there, then executes
`tests/test.sh`, which writes the reward to `/logs/verifier/reward.txt`. Almost
every rule below follows directly from that flow.

## Categories

Pick one domain for your task:

- **SWE** (software engineering): implement or fix a feature in a library or service.
- **DevOps**: build pipelines, container or IaC config, deployment tooling.
- **SRE**: reliability, observability, incident response, failure handling.
- **Data Science**: data cleaning, analysis, feature pipelines, metrics.
- **MLE** (machine learning engineering): training, evaluation, serving, or model plumbing.

Start from the blank skeleton in `tasks/_template/`; `docs/TASK-SPEC.md` is the
full contract.

## Prerequisites

- Docker, running locally.
- harbor: `uv tool install harbor`
- ruff: `uv tool install ruff`
- GitHub CLI, authenticated: `gh auth login`
- An E2B account. Sign up at https://e2b.dev, create an API key, and put it in a
  `.env` file at the repo root:

  ```
  E2B_API_KEY=your-key-here
  ```

## A task has four parts

```
tasks/<slug>/
  task.toml             metadata and the resource contract (version = "2.0")
  instruction.md        the problem statement
  environment/          Dockerfile + starter code (copied to /app/src)
  solution/solve.sh     the oracle: edits /app/src into the correct solution
  tests/test.sh         writes reward 1/0 to /logs/verifier/reward.txt
  tests/test_outputs.py the held-back pytest verifier (>= 30 cases)
```

`docs/TASK-SPEC.md` is the full contract.

## Build and check locally

Scaffold from the template and branch:

```bash
cp -r tasks/_template tasks/<slug>
git checkout -b task/<slug>
```

Author the task, then check it yourself with harbor and ruff:

```bash
harbor run --path tasks/<slug> --agent oracle   # must reach reward 1
harbor run --path tasks/<slug> --agent nop      # must reach reward 0
ruff check tasks/<slug>
```

## Raise the PR

When the task is ready, commit it and open a draft PR:

```bash
git add tasks/<slug> && git commit -m "Add task: <slug>"
git push -u origin task/<slug>
gh pr create --draft --title "Add task: <slug>" --body "Task submission for <slug>."
```

Before marking the PR ready for review, confirm the oracle reaches reward `1`,
the nop reaches reward `0`, and ruff is clean. Keep the PR focused on a single
task under `tasks/<slug>/`.

In your PR description, include:

- The task slug and category.
- A short summary of the bug or missing behavior.
- Why the task is non-trivial.
- What common incorrect solution your verifier catches.
- The local results for oracle, nop, and ruff.

## Criteria

- Oracle reward `1`, untouched nop reward `0`.
- ruff is clean.
- `task.toml` is schema-clean: `version = "2.0"`, the four sections, the required
  metadata, `difficulty` not `easy` (python tasks must be `hard`), `codebase_size`
  `small` or `large` matching the real `environment/` file count,
  `allow_internet = false`, timeouts `<= 1800`.
- The Dockerfile pins its base image, installs `tmux` and `asciinema`, and is
  hermetic (no network at run time).
- The verifier runs the agent's code, has at least 30 cases including edge cases
  and one that only the correct solution passes, and every test has a docstring.
- The instruction states the expected behavior without naming the test or the fix.
- The task is original and non-trivial; classic kata or one-bug toy tasks are not
  accepted.

## What Makes A Strong Task

Passing the oracle, nop, and ruff checks is required, but it is not enough. The
task should be a meaningful evaluation of an AI coding agent's ability to reason
through a real engineering problem.

A strong task should:

- Exercise real engineering judgment across multiple files or interacting
  behaviors.
- Require a non-trivial fix, not only a one-line condition change.
- Have a starter implementation that passes some baseline behavior but fails the
  intended broken or missing behavior.
- Include at least 30 meaningful verifier cases, not just repeated variants of
  the same assertion.
- Cover happy paths, edge cases, invalid inputs, and at least one case that
  catches a common naive or shallow fix.
- Test observable behavior only, not private implementation details or source
  text.
- Have clear instructions that describe the expected behavior without revealing
  the exact fix.

Good task domains include scheduling, retries, indexing, pricing logic, stateful
systems, persistence, concurrency, non-trivial parsing, data cleaning, metrics,
and multi-step business rules.

## Common Reasons For Rejection

- The task is too easy or resembles a common kata.
- The solution is a one-line fix with little reasoning required.
- The verifier has many cases but only tests one behavior.
- The tests are brittle or inspect implementation details.
- The instruction gives away the fix.
- The task depends on network access or unpinned runtime setup.

`docs/EVALUATION.md` is the grader's rubric.
