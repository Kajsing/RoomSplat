# Project Documentation and Status

## Current status

Status: Milestone 0 scaffolded; Milestone 1 skeleton implemented; Milestone 2 local project storage implemented; Milestone 3 video import and frame extraction implemented.
Current milestone: Milestone 4 - Reconstruction spike.

## Latest completed milestone

Milestone 3 - Video import and frame extraction.

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
- Frame extraction tests use deterministic animated GIF fixtures; general video formats require `ffmpeg` on PATH or `ROOMSPLAT_FFMPEG_PATH`.
- Frame extraction is synchronous until the Milestone 5 job system exists.
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
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 13 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Milestone 3

## Next step

Start Milestone 4: run the reconstruction spike and select/document the first practical local Windows-native Gaussian Splatting / NeRF path. Do not claim placeholder outputs are real reconstruction.

## Milestone 3 notes

- Backend now supports raw video upload with `POST /projects/{project_id}/videos/upload?filename=...`.
- Backend now supports synchronous frame extraction with `POST /projects/{project_id}/frames/extract`.
- Uploaded videos are copied into project `input/`.
- Video import metadata is written to `metadata/video_import.json`.
- Extracted frames are written to `frames/frame_*.png`.
- Frame extraction metadata is written to `metadata/frame_extraction.json`.
- Synthetic/tiny media tests generate animated GIF fixtures in temporary test folders.
- General `.mp4`, `.mov`, `.avi`, `.mkv`, and `.webm` extraction requires `ffmpeg` on PATH or configured through `ROOMSPLAT_FFMPEG_PATH`.
- Frontend now supports selecting a project, uploading video, configuring stride/max frames, and showing extraction metadata.

## Milestone 2 notes

- Backend now supports `POST /projects` and `GET /projects`.
- Project folders are created under the configured data directory using UUID project IDs.
- Each project contains `input/`, `frames/`, `reconstruction/`, `exports/`, and `metadata/`.
- Project metadata is written to `metadata/project.json`.
- Data directory config reads `ROOMSPLAT_DATA_DIR`, then `DATA_DIR`, then defaults to `data`.
- Frontend now has a create/list project flow.
- In this shell, direct Vite CLI was the reliable frontend validation path because `npm` is unavailable and bundled `pnpm` enforces build-script approval checks.
