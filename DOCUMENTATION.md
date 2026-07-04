# Project Documentation and Status

## Current status

Status: Milestone 0 scaffolded; Milestone 1 skeleton implemented; Milestone 2 local project storage implemented.
Current milestone: Milestone 3 - Video import and frame extraction.

## Latest completed milestone

Milestone 2 - Local project storage.

## How to run

Start the backend:

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
uvicorn app.main:app --app-dir backend --reload
```

Start the frontend:

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

## How to test

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

## Decisions made

| Date | Decision | Reason |
|---|---|---|
| 2026-04-30 | Local hosted web app | Keeps Android as capture device and avoids mobile performance constraints. |
| 2026-04-30 | Windows-native first | Matches primary user environment. |
| 2026-04-30 | Gaussian Splatting / NeRF first | Project owner selected splat/NeRF direction over traditional-only point cloud reconstruction. |
| 2026-04-30 | Video import before stream | Reduces MVP complexity and creates reproducible test inputs. |
| 2026-04-30 | Browser + desktop debug viewer | Browser is user-facing; desktop viewer helps pipeline debugging. |
| 2026-04-30 | `.ply` + `.glb` exports | Open formats useful for point clouds/splats and broader 3D tooling. |

## Known issues

- Frontend validation used bundled `pnpm` because `npm` is not available on PATH in this shell.
- Pipeline tests for frame extraction are still placeholders and do not exercise real media handling yet.
- Video import and frame extraction services are placeholders.
- No reconstruction pipeline selected yet.
- `.ply` may mean point cloud or splat data depending on pipeline stage; UI must label this.
- `.glb` export path is uncertain until representation is known.
- Windows-native GPU dependencies may be difficult.

## Commands run

- `python --version`
- `node --version`
- `python -m pytest backend/tests`
- `npm --prefix frontend run build`
- `C:\Users\chrkaj\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed
- `npm --prefix frontend run build` - not run in this shell because `npm` is not on PATH
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 7 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed

## Next step

Implement Milestone 3 as the next vertical slice: import a local video into a selected project `input/` directory, record import metadata, add a real frame extraction service/script with synthetic or tiny media tests, and expose the upload/extraction status in the frontend. Do not start reconstruction work until video import and frame extraction are validated.

## Milestone 2 notes

- Backend now supports `POST /projects` and `GET /projects`.
- Project folders are created under the configured data directory using UUID project IDs.
- Each project contains `input/`, `frames/`, `reconstruction/`, `exports/`, and `metadata/`.
- Project metadata is written to `metadata/project.json`.
- Data directory config reads `ROOMSPLAT_DATA_DIR`, then `DATA_DIR`, then defaults to `data`.
- Frontend now has a create/list project flow.
- In this shell, direct Vite CLI was the reliable frontend validation path because `npm` is unavailable and bundled `pnpm` enforces build-script approval checks.
