# Project Documentation and Status

## Current status

Status: Milestone 0 scaffolded; Milestone 1 skeleton implemented; Milestone 2 local project storage implemented; Milestone 3 video import and frame extraction implemented; Milestone 4 adapter-first reconstruction spike implemented; Milestone 5 local job system implemented; Milestone 6 artifact viewer integration implemented; Milestone 7 export service implemented; Milestone 8 v1 hardening and security baseline implemented; Splat-first Three.js browser viewer implemented; Usable 3D Viewer Preview implemented.
Current milestone: Usable 3D Viewer Preview complete pending final validation and push.

## Latest completed milestone

Usable 3D Viewer Preview.

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
- Placeholder exports are available for reconstruction spike debug reports only when explicitly requested; they are labeled as placeholders and are not real reconstruction output.
- Frame Room Cloud artifacts are debug viewer point clouds sampled from extracted frames and are not real reconstruction output.
- Frame Room Cloud debug preview supports `max_points`, `frame_step`, `arc_degrees`, and `plane_width`; invalid values are rejected by the worker.
- Windows-native GPU dependencies may be difficult.
- v1 remains unauthenticated and should bind to `127.0.0.1`; do not expose the backend to untrusted networks.
- API responses still include some absolute local paths for operator/debug transparency; keep this local-only or revise before shared/network use.
- Frame Room Cloud generation is capped at 50,000 points for browser responsiveness; large real artifacts should still be downloaded for full inspection when needed.

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
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_jobs.py backend/tests/test_artifacts.py` - passed, 23 tests after Usable 3D Viewer backend changes
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 4 frontend helper tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Usable 3D Viewer frontend changes with chunk-size warning
- Browser smoke at `http://127.0.0.1:5173` after Usable 3D Viewer changes - passed with Objectron custom debug preview params: 12,000 max points, frame step 2, 90 degree arc, 1.8 plane width
- Browser smoke generated `metadata/debug_frame_cloud.json` with 4 frame planes and 11,656 sampled points
- Browser pixel check for `data/manual-verification/usable-viewer-preview.png` - nonblank canvas crop, 44 unique colors, non-background ratio 1.0
- Browser verified large-view mode, camera presets, grid/axes/frame marker toggles, point-size stepper, color mode, screenshot status, artifact switching, and not-reconstruction warning
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 51 tests for final Usable 3D Viewer validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 4 frontend helper tests for final Usable 3D Viewer validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed for final Usable 3D Viewer validation with chunk-size warning
- `pnpm dlx npm@latest --prefix frontend audit --audit-level=moderate` - passed, 0 vulnerabilities
- `git diff --check` - passed with line-ending warnings only
- Codex Security config preflight for `security_scan` - ready after declaring native v1 multi-agent runtime from tool surface
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 37 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Milestone 8
- `pnpm dlx npm@latest --prefix frontend install three @mkkellogg/gaussian-splats-3d` with bundled Node on PATH - passed
- `pnpm dlx npm@latest --prefix frontend install -D vite@latest` with bundled Node on PATH - passed, npm audit advisories cleared
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_video_import.py backend/tests/test_jobs.py backend/tests/test_artifacts.py` - passed, 21 tests
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed with chunk-size warning after Three.js viewer
- `POST /projects/9522ce63dbfc454fb638fae38375863c/jobs` with `debug_frame_cloud` - passed, generated 46,464 debug points
- Browser smoke at `http://127.0.0.1:5173` - passed; Three.js canvas nonblank and viewer controls/artifact switching verified
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 42 tests after Splat-first viewer
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after Splat-first viewer with chunk-size warning
- `pnpm dlx npm@latest --prefix frontend audit --audit-level=moderate` - passed, 0 vulnerabilities
- `git diff --check` - passed with line-ending warnings only

## Next step

Recommended next milestone: real reconstruction dependency setup, import/viewer polishing for larger artifacts, or a minimal end-to-end sample project pack.

## Usable 3D Viewer Preview notes

- Extended `debug_frame_cloud` job params: `max_points`, `frame_step`, `arc_degrees`, and `plane_width`.
- Added strict backend validation for debug preview params.
- Added deterministic frame-plane sampling and metadata records with source frame, plane position, angle, point count, and plane/image size.
- Added `GET /projects/{project_id}/debug-frame-cloud` for viewer metadata.
- Added backend tests for param acceptance, invalid limits, deterministic output, frame-plane metadata, metadata endpoint, artifact labeling, and path containment.
- Added frontend debug preview controls for custom Frame Room Cloud params.
- Added Three.js viewer large-view mode, camera presets, screenshot capture, artifact stats, frame markers, improved empty/error states, and clearer splat fallback diagnostics.
- Added artifact URL cache-busting with `modified_at` so regenerated PLY artifacts do not show stale browser-cached geometry.
- Added point-size stepper buttons next to the slider for more reliable keyboard/pointer control.
- Added frontend helper tests for artifact labels, supported modes, and stats byte formatting.
- Frame Room Cloud remains explicitly debug/inspection-only and not reconstruction.

## Splat-first viewer notes

- Added frontend dependencies `three` and `@mkkellogg/gaussian-splats-3d`.
- Upgraded Vite to resolve current npm audit advisories reported after dependency installation.
- Added `debug_frame_cloud` job type.
- Added `GET /projects/{project_id}/frames/extraction` so the frontend can detect existing extracted-frame metadata.
- Added `debug_frame_cloud_ply` artifact label.
- Added `backend/app/services/debug_frame_cloud.py`.
- The debug-frame-cloud job reads `metadata/frame_extraction.json` and sampled frame images, then writes `reconstruction/debug-frame-room.ply` and `metadata/debug_frame_cloud.json`.
- Frame Room Cloud is deterministic, ASCII PLY with XYZ + RGB, capped at 50,000 points, and arranged as vertical frame planes along a shallow arc.
- Frame Room Cloud metadata includes `mode: debug` and `not_reconstruction: true`.
- Added a React/Three.js `ThreeViewer` with OrbitControls, grid, axes, lights, reset camera, fit, point size, color mode, and artifact warning labels.
- `splat_ply` attempts GaussianSplats3D first and falls back to point-cloud rendering with an explicit message if the file is not loadable as splat data.
- `mesh_glb` now loads through Three.js `GLTFLoader` instead of metadata-only preview.
- Debug reports remain text views and are not treated as 3D artifacts.
- Manual browser smoke used the Objectron cup project and generated `data/manual-verification/viewer-smoke.png` as an ignored screenshot artifact.
- Browser pixel check found the Three.js canvas nonblank with 3,363 unique colors in the canvas crop.
- Manual browser controls tested: grid/axes toggles, color mode, point size, reset camera, fit, artifact switching, and orbit/zoom pointer interaction.

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
- ASCII PLY artifacts originally rendered in a 2D canvas preview; the current viewer uses Three.js through `ThreeViewer`.
- Splat PLY uses the same debug point preview but keeps an explicit splat label.
- GLB artifacts originally received a metadata preview; the current viewer loads GLB scene artifacts through Three.js `GLTFLoader`.
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
