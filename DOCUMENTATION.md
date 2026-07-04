# Project Documentation and Status

## Current status

Status: Milestone 0 scaffolded; Milestone 1 skeleton implemented; Milestone 2 local project storage implemented; Milestone 3 video import and frame extraction implemented; Milestone 4 adapter-first reconstruction spike implemented; Milestone 5 local job system implemented; Milestone 6 artifact viewer integration implemented; Milestone 7 export service implemented; Milestone 8 v1 hardening and security baseline implemented.
Current milestone: v1 baseline complete; next milestone should be selected by project owner.

## Latest completed milestone

Milestone 8 - v1 hardening and security baseline.

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
- Synchronous frame extraction API still exists for compatibility, but the UI now starts frame extraction through jobs.
- No real reconstruction training is integrated yet; Milestone 4 selects an interim path and reports dependency readiness.
- Local reconstruction dependencies are not installed in the current shell: `pycolmap`, `nerfstudio`, `gsplat`, `torch`, `open3d`, `colmap`, `ns-process-data`, and `ns-train` are unavailable.
- Windows-native Nerfstudio/gsplat setup may be fragile due to CUDA, PyTorch, and Visual Studio Build Tools requirements.
- `.ply` may mean point cloud or splat data depending on pipeline stage; UI must label this.
- `.glb` export path is uncertain until representation is known.
- Full in-browser GLB mesh rendering is not implemented yet; GLB artifacts get a metadata preview and download link.
- Placeholder exports are available for reconstruction spike debug reports only when explicitly requested; they are labeled as placeholders and are not real reconstruction output.
- Windows-native GPU dependencies may be difficult.
- v1 remains unauthenticated and should bind to `127.0.0.1`; do not expose the backend to untrusted networks.
- API responses still include some absolute local paths for operator/debug transparency; keep this local-only or revise before shared/network use.
- Browser PLY preview is intentionally limited for responsiveness; large artifacts should be downloaded for full inspection.

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
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 17 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe pipeline\scripts\run_reconstruction_spike.py --help` - passed
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Milestone 4
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 23 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Milestone 5
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 26 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Milestone 6
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_artifacts.py backend/tests/test_exports.py` - passed, 9 tests
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 33 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Milestone 7
- `git diff --check` - passed with line-ending warnings only
- Codex Security config preflight for `security_scan` - ready after declaring native v1 multi-agent runtime from tool surface
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 37 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Milestone 8

## Next step

Select the next milestone. Good candidates: real reconstruction dependency setup, full Three.js GLB rendering, or a minimal end-to-end sample project pack.

## Milestone 8 notes

- Expanded README into a Windows-oriented setup, configure, run, workflow, test, capture, and output guide.
- Updated `.env.example` with documented data directory, ffmpeg path, max upload size, ffmpeg timeout, localhost binding, and Vite API URL settings.
- Added `docs/security-baseline.md`.
- Added upload size enforcement with `ROOMSPLAT_MAX_UPLOAD_MB`.
- Added ffmpeg timeout handling with `ROOMSPLAT_FFMPEG_TIMEOUT_SECONDS`.
- Added reconstruction job path containment for `frames_dir`.
- Added artifact listing containment so escaped symlinks are not listed as artifacts.
- Added frontend API URL support through `VITE_ROOMSPLAT_API_URL` / `VITE_BACKEND_URL`.
- Added browser PLY preview size limit.
- Updated capture, risk, validation, architecture, and project-format docs for v1 hardening.
- Security baseline found no critical/high issues after the Milestone 8 fixes; residual risks remain around local-only/no-auth use, media resource usage, absolute path disclosure, and future adapter safety.

## Milestone 7 notes

- Added `POST /projects/{project_id}/exports`.
- Added `GET /projects/{project_id}/exports`.
- Real PLY/GLB exports copy existing same-format artifacts into `exports/`.
- Export metadata is written to `metadata/exports/<export-id>.json`.
- Export metadata records source artifact, source path, export path, format, generated time, artifact label, download URL, warning, and `real`/`placeholder` status.
- Placeholder PLY/GLB exports can be created only from the reconstruction spike debug report and only with `allow_placeholder: true`.
- Placeholder files and metadata include explicit warnings that they are not real reconstruction output.
- The frontend artifact viewer now exposes export controls and refreshes/selects exported artifacts after export.

## Milestone 6 notes

- Added artifact discovery under `GET /projects/{project_id}/artifacts`.
- Added artifact serving under `GET /projects/{project_id}/artifacts/{artifact_id}/download`.
- Artifact labels include `point_cloud_ply`, `splat_ply`, `mesh_glb`, `debug_report`, and `unsupported`.
- Frontend viewer can select listed artifacts.
- ASCII PLY artifacts render in a canvas preview with rotate/zoom controls.
- Splat PLY uses the same debug point preview but keeps an explicit splat label.
- GLB artifacts get a metadata preview and download link; full Three.js GLB mesh rendering remains future work.
- `reconstruction_spike.json` is shown as a debug report, not as a reconstructed artifact.

## Milestone 5 notes

- Added durable job metadata under `metadata/jobs/<job-id>.json`.
- Added per-job logs under `metadata/jobs/<job-id>.log`.
- Added job statuses: `queued`, `running`, `succeeded`, `failed`.
- Added job types: `frame_extraction` and `reconstruction_spike`.
- Added `POST /projects/{project_id}/jobs`, `GET /projects/{project_id}/jobs`, and `GET /projects/{project_id}/jobs/{job_id}`.
- Added a local thread-pool worker for background execution.
- Frame extraction jobs call the existing `FrameExtractionService`.
- Reconstruction-spike jobs call the adapter-first spike and write `metadata/reconstruction_spike.json`.
- Failed jobs preserve error messages and log entries.
- Frontend now starts frame extraction as a job, polls active job status, lists recent jobs, and can start a reconstruction-spike job.

## Milestone 4 notes

- Added a reconstruction adapter contract under `pipeline/adapters/`.
- Added adapter assessments for COLMAP/pycolmap, Nerfstudio Splatfacto, gsplat, and Open3D debug tooling.
- Added `pipeline/scripts/run_reconstruction_spike.py`.
- The selected interim path is `frames -> COLMAP/pycolmap poses -> Nerfstudio Splatfacto -> splat.ply`.
- The selected path is intentionally replaceable by a faster learned/generative splat adapter later.
- The spike validates project frames, reports dependency readiness, declares output contracts, and can write `metadata/reconstruction_spike.json`.
- No fake reconstruction artifacts are produced.
- Primary references checked:
  - https://docs.nerf.studio/quickstart/installation.html
  - https://docs.nerf.studio/nerfology/methods/splat.html
  - https://colmap.github.io/pycolmap/index.html
  - https://colmap.github.io/
  - https://github.com/nerfstudio-project/gsplat/blob/main/docs/INSTALL_WIN.md
  - https://www.open3d.org/docs/release/getting_started.html

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
