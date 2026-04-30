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
3. Update `DOCUMENTATION.md` with:
   - milestone status,
   - commands run,
   - test results,
   - decisions made,
   - known issues,
   - next step.
4. Add a `.logs/YYYY-MM-DD-milestone-N.md` entry if useful.

## Error handling philosophy

- Fail loudly with actionable messages.
- Preserve job logs.
- Do not swallow external tool errors.
- Surface missing dependency errors clearly in the UI and CLI.
- Avoid destructive cleanup unless explicitly requested.

## Dependency policy

- Prefer widely used open-source dependencies.
- Ask before adding paid/commercial tools as required dependencies.
- Optional integrations may be documented but must not block base app startup.
- Do not require cloud services.

## Security and filesystem policy

- Treat imported files as untrusted.
- Do not allow arbitrary file writes outside the configured data directory.
- Sanitize project names for filesystem use.
- Do not expose the local server publicly by default.
- Bind to localhost by default.

## Stop and ask when

- A milestone requires a major architecture change.
- External dependencies conflict with Windows-native execution.
- Reconstruction requires a paid/commercial CLI.
- GPU requirements exceed reasonable local assumptions.
- A user-facing decision affects project direction.
