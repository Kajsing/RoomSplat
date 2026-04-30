# Implementation Plan

## Milestone 0 — Repository scaffold and docs

Goal: Create the repo structure, project docs, ignored data folders, and minimal build/test setup.

Acceptance criteria:

- `AGENTS.md`, `PLAN.md`, `IMPLEMENT.md`, `DOCUMENTATION.md`, `SPEC.yaml`, `ARCHITECTURE.md`, and `README.md` exist.
- Backend, frontend, pipeline, docs, examples, data, and `.logs` directories exist.
- `.gitignore` excludes generated data, Python caches, node modules, build outputs, videos, frames, models, splats, and exports.
- `DOCUMENTATION.md` records the initial status.

Validation:

```bash
python --version
node --version
```

## Milestone 1 — Minimal local hosted web app

Goal: Start a local FastAPI backend and Vite frontend.

Acceptance criteria:

- Backend exposes `GET /health` returning JSON status.
- Frontend loads in browser and displays backend health.
- README includes Windows startup commands.
- Backend test covers `/health`.

Validation:

```bash
python -m pytest backend/tests
npm --prefix frontend run build
```

## Milestone 2 — Local project storage
Goal: Create and list local scan projects.

## Milestone 3 — Video import and frame extraction
Goal: Import a video file and extract frames into the project folder.

## Milestone 4 — Reconstruction spike: Gaussian Splatting / NeRF path
Goal: Determine and document the first working local Windows-native reconstruction path.

## Milestone 5 — Job system for long-running reconstruction
Goal: Add local background jobs for extraction and reconstruction.

## Milestone 6 — Viewer integration
Goal: Display exported `.ply` and/or `.glb` results.

## Milestone 7 — Export service
Goal: Provide export links for `.ply` and `.glb`.

## Milestone 8 — v1 hardening and docs
Goal: Make the app understandable, reproducible, and safe for public Git release.
