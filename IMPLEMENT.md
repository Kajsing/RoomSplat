# Implementation Runbook

## Before coding
1. Read `AGENTS.md`.
2. Read `SPEC.yaml`.
3. Read `PLAN.md`.
4. Read `ARCHITECTURE.md`.
5. Read `DOCUMENTATION.md`.
6. Identify the current milestone.
7. Write a short entry in `.logs/` if the task is non-trivial.

## During coding
- Work on one milestone at a time.
- Keep diffs scoped.
- Prefer small, testable functions.
- Keep external tool integration behind adapters.
- Use placeholders only when clearly labeled as placeholders.
- Never present fake reconstruction output as real.
- Update docs when behavior changes.

## After each milestone
1. Run the milestone validation commands from `PLAN.md`.
2. Fix failures before moving on.
3. Update `DOCUMENTATION.md`.
4. Add a `.logs/YYYY-MM-DD-milestone-N.md` entry if useful.
