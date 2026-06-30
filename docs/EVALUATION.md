# Evaluation Rubric

The grader fills this in once per submission. The objective gates are reproduced
with Harbor and ruff; the rest is human judgement.

## How to grade

1. Check out the candidate's PR branch.
2. Reproduce the objective gates. Never trust the candidate's numbers:

   ```bash
   harbor run --path tasks/<slug> --agent oracle
   harbor run --path tasks/<slug> --agent nop
   ruff check tasks/<slug>
   ```

   The task passes the objective gate only when ruff is clean, the oracle scores
   1, the nop scores 0, and the task satisfies the static contract in
   `docs/TASK-SPEC.md`.
3. Score the MANUAL items below by reading the task.

The commands above reproduce the automated reward checks; this rubric covers
what a human grader scores by hand.

## Objective gate

| Gate | Source | Pass condition |
| --- | --- | --- |
| Oracle reward 1 | C1.1 | the oracle solves the task |
| Nop reward 0 | C1.2 | the untouched starter fails the verifier |
| ruff clean | - | the task code lints clean |
| Static contract | A1.*-A5.*, B1.1 | the task follows `docs/TASK-SPEC.md` |

If the objective gate fails, the submission is rejected regardless of the rest.

## Human rubric

| # | Criterion | Weight | Notes |
| --- | --- | --- | --- |
| 1 | Original and non-trivial (B4.7) | 20 | genuine, non-trivial engineering work |
| 2 | Verifier is real and robust (B2.1, B2.3) | 25 | runs the code; >=30 cases; edge + would-regress |
| 3 | Two-way coverage (B2.2) | 10 | every behavior tested and described |
| 4 | Non-brittle assertions (B2.4) | 10 | no logs/private fields/order/timing |
| 5 | Instruction quality (B4.3) | 15 | the what, not the how; no leak |
| 6 | Measured difficulty (C2) | 20 | run frontier agents; python must land Hard |
| | Total | 100 | |

## Scoring sheet

| Item | Score | Notes |
| --- | --- | --- |
| Objective gate (PASS/FAIL) | | |
| 1 Original | /20 | |
| 2 Verifier | /25 | |
| 3 Coverage | /10 | |
| 4 Non-brittle | /10 | |
| 5 Instruction | /15 | |
| 6 Difficulty | /20 | |
| Total | /100 | |
