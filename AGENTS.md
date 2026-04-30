# Local 3D Room Mapper — Agent Instructions

## Project role

You are implementing a local Windows-first 3D reconstruction web app. The app imports video, extracts frames, runs a local Gaussian Splatting / NeRF-style reconstruction pipeline, and exports `.ply` and `.glb` outputs.

## Sources of truth

Read these before changing code:

1. `SPEC.yaml` — product and technical requirements.
2. `PLAN.md` — milestone sequence, acceptance criteria, validation commands.
3. `IMPLEMENT.md` — execution rules.
4. `ARCHITECTURE.md` — module boundaries and data flow.
5. `DOCUMENTATION.md` — current status, decisions, known issues.

If these files conflict, follow this precedence:

1. User prompt.
2. `AGENTS.md`.
3. `SPEC.yaml`.
4. `PLAN.md`.
5. `IMPLEMENT.md`.
6. Other docs.

## Working rules

- Keep diffs scoped to the current milestone.
- Do not silently expand product scope.
- Prefer a minimal working vertical slice over broad unfinished scaffolding.
- Run validation commands after each milestone.
- Fix failing validations before moving to the next milestone.
- Update `DOCUMENTATION.md` after meaningful changes.
- Log work under `.logs/` when a task involves investigation, tradeoffs, or multiple attempts.
- Keep generated data out of Git.
- Do not commit videos, extracted frames, trained splats, model checkpoints, or large exports.
- Do not add cloud dependencies unless explicitly requested.
- Do not require Docker for v1 unless Windows-native execution proves impractical.

## Technical defaults

- Backend: Python + FastAPI.
- Frontend: Vite + React + TypeScript.
- Viewer: browser-based Three.js viewer plus optional Open3D debug tools.
- Runtime: Windows native first.
- Long-running work: local job queue / background worker.
- Storage: local project folders under a configurable data directory.
- Exports: `.ply` and `.glb`.
- Reconstruction direction: Gaussian Splatting / NeRF first, using existing tools where practical.

## Stop conditions

Stop and ask for clarification if:

- A selected core decision is impossible without changing product direction.
- A new paid/commercial dependency is required.
- A dependency requires cloud upload.
- A change would require committing large binary data.
- Validation cannot be made to pass after reasonable focused repair.

## Validation expectations

At minimum, keep these working:

- Backend health endpoint test.
- Frontend build.
- Frame extraction test using synthetic or tiny sample media.
- Export contract tests for `.ply` and `.glb` placeholder outputs.
- End-to-end smoke path: create project → upload/import video placeholder → extract frames → create job → produce/export placeholder or real artifact depending on milestone.
