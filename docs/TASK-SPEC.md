# Harbor Task Specification

This is the contract every task in this repository must satisfy. It is the
source of truth.

## What a Harbor task is

A Harbor task is a self-contained unit that evaluates a coding agent. The agent
wakes up inside a container, reads a problem statement, edits the code, and is
then graded by an automated verifier. A task has four parts:

| Part | Path | Role |
| --- | --- | --- |
| Environment | `environment/` | A Dockerfile plus starter code. The world the agent wakes up in. |
| Instruction | `instruction.md` | The human-readable problem statement handed to the agent. |
| Solution | `solution/solve.sh` | The oracle. A script that performs the correct solution. |
| Tests | `tests/` | The verifier. Runs checks and writes a reward. |

## The reward invariant

Every task is judged by one invariant:

- The **oracle** solution scores reward `1`.
- An **untouched starter** (the nop agent, which changes nothing) scores reward `0`.

Run both agents with Harbor to check this invariant:

```bash
harbor run --path tasks/<slug> --agent oracle
harbor run --path tasks/<slug> --agent nop
```

A task that does not satisfy this is not a valid task. The invariant proves two
things at once: the task is solvable (the oracle reaches `1`) and the verifier is
not trivially satisfied (the nop stays at `0`).

## Directory layout

```
tasks/<slug>/
  task.toml            # metadata and the resource contract
  instruction.md       # the problem statement
  environment/
    Dockerfile         # single-stage build of the agent's world
    .dockerignore
    <starter code>     # the files the agent edits
  solution/
    solve.sh           # the oracle
  tests/
    test.sh            # writes the reward
    test_outputs.py    # the pytest verifier
```

`<slug>` is lowercase and hyphen-separated, and it matches the task directory
name. Harbor uses the directory name as the task identifier when `task.toml`
has no `[task]` section.

## Runtime layout (inside the container)

The build and the two scripts agree on a fixed set of paths:

| Path | What lives there |
| --- | --- |
| `/app/src` | The starter code, copied from `environment/` at build time. The agent edits files here. |
| `/solution` | `solution/`, copied in for the oracle agent only. The oracle runs `/solution/solve.sh`. |
| `/tests` | `tests/`, copied in by the verifier after the agent runs. The verifier runs `/tests/test.sh`. |
| `/logs/verifier/reward.txt` | The single reward number the verifier writes. |

`tests/` and `solution/` are never baked into the image. They are mounted at run
time, after the agent has finished, so the agent cannot read the tests or the
oracle while it works.

## task.toml

Schema version `2.0`. Render real values and keep the section order.

```toml
version = "2.0"

[metadata]
author_name = "candidate-name"
author_email = "candidate@email"
category = "software-engineering"   # software-engineering | debugging
subcategories = []                  # field must exist even if empty
difficulty = "hard"                 # medium | hard | unknown (easy not allowed; python must be hard)
codebase_size = "small"             # small (20-199) | large (200+); minimal is blocked for new tasks; must match environment/ file count
number_of_milestones = 0
languages = ["python"]              # the agent-facing language(s)
tags = ["strings", "parsing"]       # 3 to 6 keywords
expert_time_estimate_min = 30
junior_time_estimate_min = 90       # junior >= expert

[verifier]
timeout_sec = 600                   # <= 1800, and >= agent.timeout_sec

[agent]
timeout_sec = 600                   # <= 1800

[environment]
build_timeout_sec = 600
cpus = 1
memory_mb = 2048
storage_mb = 4096
allow_internet = false              # tasks are hermetic; all deps installed at build time
```

Rules:

- `version` is exactly `"2.0"`.
- All four sections (`metadata`, `verifier`, `agent`, `environment`) are present.
- `difficulty` is one of `medium`, `hard`, `unknown`. `easy` is not allowed, and
  any task with `python` in `languages` must be `hard`.
- `subcategories` exists even when empty.
- `codebase_size` matches the actual file count under `environment/` (small is
  20-199 files, large is 200+). `minimal` is blocked for new tasks.
- `allow_internet = false`. Tasks are hermetic.
- `verifier.timeout_sec >= agent.timeout_sec`, and both are `<= 1800`.
- `junior_time_estimate_min >= expert_time_estimate_min`.
- `tags` holds 3 to 6 keywords.

## environment/Dockerfile

Single stage. Install the agent toolchain and the verifier's `python3` plus
pytest at build time. `tmux` and `asciinema` are required; without them the
harness reports `verifier_did_not_run`. Pin the base image to an official
version.

```dockerfile
FROM python:3.12-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux asciinema ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/test-venv && \
    /opt/test-venv/bin/pip install --no-cache-dir pytest==8.3.3

COPY . /app/src
WORKDIR /app/src
```

Not allowed in the Dockerfile:

- `--platform` in `FROM`.
- `CMD` or `USER`.
- `COPY . .` from the repo root. Copy only the build context with
  `COPY . /app/src`. The build context is `environment/`, so the tests and the
  solution never enter the image.
- `COPY tests/` or `COPY solution/`.
- apt exact-version pins such as `pkg=1.2.3`.
- `--privileged`.
- `mkdir -p` of `/tests`, `/solution`, `/oracle`, or `/logs/verifier`. Those are
  mounted at run time.

`.dockerignore` drops the usual noise: `.git`, `__pycache__`, `*.pyc`, `.venv`,
`node_modules`, and build output.

## solution/solve.sh

The oracle session. It edits the starter in place under `/app/src` to produce
the correct solution, deterministically and idempotently. Running it twice
yields the same result.

- `set -euo pipefail` is allowed here. This is not `test.sh`.
- Heredocs are allowed.
- No `if [ -d /oracle ]` style branches. No writing the answer to a side file.
  The oracle solves the task the way a correct agent would.

## tests/

`tests/` holds exactly two files: `test.sh` and `test_outputs.py`. No other
files and no subdirectories.

### test.sh (the reward contract)

`test.sh` runs the verifier and writes a single number to
`/logs/verifier/reward.txt`. It must end on the reward block's `fi`. Use this
shape verbatim:

```bash
#!/bin/bash
mkdir -p /logs/verifier
/opt/test-venv/bin/pytest /tests/test_outputs.py -rA -v
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
```

Not allowed in `test.sh`:

- `set -e` or `set -euo pipefail`. They abort the script before the reward is
  written.
- Heredocs.
- A trailing `exit 0`.
- Re-running `solve.sh`.
- Any runtime dependency install: `pip`, `npm`, `apt`, `apt-get`, `curl`,
  `wget`, or `git clone`. Every dependency is installed at Docker build time.

### test_outputs.py (the verifier)

- Tests assert observable behavior by running the agent's code, not by grepping
  the source for a magic string.
- Every `def test_*` carries a one-line docstring.
- Import the code under test from `/app/src`.
- Cover the happy path, empty and boundary inputs, and at least one case that
  regresses to the original buggy behavior. Aim for at least 30 cases; the
  reference task uses 35.

## Hermeticity

`allow_internet = false`. The container has no network at run time. Install
everything (agent tools, the verifier venv, pytest) during the Docker build. If
a task needs a package at run time and it was not installed at build time, the
task is broken.
