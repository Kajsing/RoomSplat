# Project Documentation and Status

## Current status

Status: Milestone 0 scaffolded; Milestone 1 skeleton implemented; Milestone 2 local project storage implemented; Milestone 3 video import and frame extraction implemented; Milestone 4 adapter-first reconstruction spike implemented; Milestone 5 local job system implemented; Milestone 6 artifact viewer integration implemented; Milestone 7 export service implemented; Milestone 8 v1 hardening and security baseline implemented; Splat-first Three.js browser viewer implemented; Usable 3D Viewer Preview implemented; Real Reconstruction Preview v1 implemented; Reconstruction Quality + Camera Path v1 implemented; Real Splat Pipeline Adapter v1 implemented; LingBot-Map-inspired learned geometry adapter readiness implemented; learned geometry import/preflight v1 implemented.
Current milestone: Real Splat Pipeline Exploration + First Local Splat Adapter v1 complete.
Next planned milestone: choose between improving native browser splat rendering/training quality or adding an optional isolated learned-model runtime adapter after checkpoint/download safety rules are finalized.

## Latest completed milestone

Real Splat Pipeline Exploration + First Local Splat Adapter v1.

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
| 2026-07-22 | Learned geometry readiness before model integration | LingBot-Map is useful inspiration, but direct runtime adoption has checkpoint, download, CUDA, Windows, server-binding, and file-containment risks. |

## Known issues

- Frontend validation used bundled `pnpm` because `npm` is not available on PATH in this shell.
- Frame extraction tests use deterministic animated GIF fixtures; general video formats require `ffmpeg` on PATH or `ROOMSPLAT_FFMPEG_PATH`.
- Synchronous frame extraction API still exists for compatibility, but the UI now starts frame extraction through jobs.
- Real sparse point-cloud reconstruction is integrated through local COLMAP; it requires `colmap.exe`/`COLMAP.bat` on PATH or `ROOMSPLAT_COLMAP_PATH`.
- Real splat training is integrated through local Nerfstudio/Splatfacto and produced the first local Objectron cup `reconstruction/splat.ply`.
- The first successful local real-splat stack is Python 3.10, PyTorch 2.1.2+cu118, Nerfstudio 1.1.5, precompiled `gsplat==1.4.0+pt21cu118`, Visual Studio Build Tools, FFmpeg, and COLMAP 3.9.1 no-CUDA under ignored local `data/tools` paths.
- COLMAP 4.1.0 works for RoomSplat sparse point-cloud jobs, but Nerfstudio 1.1.5 process-data expects older `SiftExtraction.use_gpu`; local splat attempts currently use COLMAP 3.9.1 no-CUDA through `ROOMSPLAT_COLMAP_PATH`.
- Windows-native Nerfstudio/gsplat setup remains fragile if gsplat falls back to source/JIT compilation; prefer a matching precompiled gsplat wheel when available.
- `.ply` may mean point cloud or splat data depending on pipeline stage; UI must label this.
- `.glb` export path is uncertain until representation is known.
- Placeholder exports are available for reconstruction spike debug reports only when explicitly requested; they are labeled as placeholders and are not real reconstruction output.
- Frame Room Cloud artifacts are debug viewer point clouds sampled from extracted frames and are not real reconstruction output.
- Frame Room Cloud debug preview supports `max_points`, `frame_step`, `arc_degrees`, and `plane_width`; invalid values are rejected by the worker.
- Windows-native GPU dependencies may be difficult.
- v1 remains unauthenticated and should bind to `127.0.0.1`; do not expose the backend to untrusted networks.
- API responses still include some absolute local paths for operator/debug transparency; keep this local-only or revise before shared/network use.
- Frame Room Cloud generation is capped at 50,000 points for browser responsiveness; large real artifacts should still be downloaded for full inspection when needed.
- Postshot Gaussian-style PLY samples with `f_dc_*` color coefficients can be shown as point-cloud fallback, but GaussianSplats3D currently times out on the local cactus Postshot sample before rendering it as real splats.
- SuperSplat compressed PLY samples use packed chunk/sh fields and no ordinary vertex `x/y/z` positions, so they need explicit compressed splat support; current point-cloud fallback cannot display them.
- Imported PLY/GLB/splat artifacts may use different up axes or appear upside down; the Three.js viewer now has source/flip/axis-conversion orientation presets for inspection.
- LingBot-Map-style learned geometry is not yet integrated. Treat it as inspiration for adapter/output contracts until RoomSplat has model checkpoint safety, dependency isolation, local-only controls, and geometry bundle validation.
- `metadata/geometry_bundle.json` now defines the first RoomSplat-native learned geometry bundle contract, but no LingBot-Map/VGGT runtime or checkpoint loader is integrated.
- Learned geometry import/preflight can normalize completed local output folders, but still does not run LingBot-Map/VGGT or load checkpoints.

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
- `where.exe colmap` - not found
- `winget search COLMAP` - no package found
- Downloaded official GitHub release asset `colmap-x64-windows-nocuda.zip` for COLMAP 4.1.0 into ignored `data/tools/`
- `C:\project\RoomSplat\data\tools\colmap-4.1.0-nocuda\bin\colmap.exe -h` - passed
- Direct `ReconstructionService.reconstruct_point_cloud` run on Objectron project `9522ce63dbfc454fb638fae38375863c` - passed with 8 input frames, 8 registered frames, 729 PLY points
- Browser smoke at `http://127.0.0.1:5173` for Real Reconstruction Preview v1 - passed; UI `Run point cloud reconstruction` job succeeded with 731 PLY points and 8 registered frames
- Browser verified `sparse-point-cloud.ply` listed as `point_cloud_ply`, reconstruction stats visible, real COLMAP notice visible, debug frame planes warning visible, artifact switching works, and fit/reset/point-size/color controls respond
- Browser screenshot saved to ignored `data/manual-verification/real-reconstruction-preview-v1.png`
- Browser pixel check for Real Reconstruction Preview v1 canvas crop - nonblank, 1,892 unique colors, non-background ratio 0.044931
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 62 tests for final Real Reconstruction Preview v1 validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 4 frontend helper tests for final Real Reconstruction Preview v1 validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed for final Real Reconstruction Preview v1 validation with chunk-size warning
- `pnpm dlx npm@latest --prefix frontend audit --audit-level=moderate` with bundled Node on PATH - passed, 0 vulnerabilities
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
- Local readiness checks for Real Splat Pipeline Adapter v1:
  - `nvidia-smi` found NVIDIA GeForce RTX 3080 Ti
  - `nvcc` not found
  - `ns-process-data`, `ns-train`, `ns-export` not found
  - backend Python 3.12.13
  - `torch`, `nerfstudio`, `gsplat`, `pycolmap`, `open3d` missing from backend Python runtime
- Direct `SplatReconstructionService.reconstruct_splat` readiness checks for cup/chair/shoe - passed as blocked diagnostics with no fake `splat.ply`
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest pipeline/tests/test_nerfstudio_splat_runner.py backend/tests/test_jobs.py backend/tests/test_artifacts.py` - passed, 40 tests after splat adapter changes
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 5 frontend helper tests after splat adapter UI changes
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after splat adapter UI changes with chunk-size warning
- Browser smoke at `http://127.0.0.1:5173` for Real Splat Pipeline Adapter v1 - passed after backend restart; UI created `reconstruct_splat`, showed `blocked_missing_dependencies`, did not show `[object Object]`, and did not list fake `splat.ply`
- Filesystem check confirmed Objectron cup has `metadata/splat_reconstruction.json` with `status: blocked_missing_dependencies`, `is_reconstruction: false`, `not_reconstruction: true`, `output_path: null`, and no `reconstruction/splat.ply`
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 76 tests for final Real Splat Pipeline Adapter v1 validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 5 frontend helper tests for final Real Splat Pipeline Adapter v1 validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed for final Real Splat Pipeline Adapter v1 validation with chunk-size warning
- `pnpm dlx npm@latest --prefix frontend audit --audit-level=moderate` - passed, 0 vulnerabilities
- `git diff --check` - passed with line-ending warnings only
- Direct `ReconstructionService.reconstruct_point_cloud` runs with local COLMAP 4.1.0 no-CUDA for Reconstruction Quality + Camera Path v1 - passed for cup/chair/shoe:
  - cup: 8 input frames, 8 registered frames, 729 PLY points, 8 cameras
  - chair: 14 input frames, 14 registered frames, 3,723 PLY points, 14 cameras
  - shoe: 10 input frames, 10 registered frames, 2,041 PLY points, 10 cameras
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest pipeline/tests/test_colmap_sparse_runner.py backend/tests/test_jobs.py backend/tests/test_artifacts.py` - passed, 39 tests after camera/path metadata changes
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 5 frontend helper tests after artifact-order changes
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after camera/path viewer changes with chunk-size warning
- Browser smoke at `http://127.0.0.1:5173` for Reconstruction Quality + Camera Path v1 - passed with Objectron cup project, `sparse-point-cloud.ply`, point/camera/path stats, toggles, real reconstruction notice, and nonblank canvas pixel check
- Browser screenshot saved to ignored `data/manual-verification/reconstruction-quality-camera-path-v1.png`
- Browser pixel check for Reconstruction Quality + Camera Path v1 canvas crop - nonblank, 3,857 unique colors, non-background ratio 0.059002
- `$env:PYTHONPATH='backend'; C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests pipeline/tests` - passed, 67 tests for final Reconstruction Quality + Camera Path v1 validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 5 frontend helper tests for final Reconstruction Quality + Camera Path v1 validation
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed for final Reconstruction Quality + Camera Path v1 validation with chunk-size warning
- `pnpm dlx npm@latest --prefix frontend audit --audit-level=moderate` - passed, 0 vulnerabilities
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
- Inspected `C:\project\3DGS_PLY_sample_data` and copied selected CC0 PLY samples into ignored local project data for browser viewer testing.
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after 3DGS sample viewer fallback changes with chunk-size warning.
- Browser smoke at `http://127.0.0.1:5173` for local 3DGS samples - Postshot cactus PLY displayed as point-cloud fallback after splat timeout; SuperSplat compressed PLY showed clear unsupported-format error.
- Pixel check for `data/manual-verification/sample-cactus-postshot-fallback-large-view.png` - nonblank screenshot crop, 22,903 unique colors.
- `$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests pipeline/tests` - passed, 79 tests after 3DGS sample viewer fallback changes.
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 5 frontend helper tests after 3DGS sample viewer fallback changes.
- `git diff --check` - passed with line-ending warnings only after 3DGS sample viewer fallback changes.
- `where.exe ns-process-data`, `where.exe ns-train`, `where.exe ns-export`, `where.exe nvcc`, `where.exe conda` - not found during first real splat goal continuation.
- `where.exe nvidia-smi` - found `C:\Windows\System32\nvidia-smi.exe`.
- Direct `SplatReconstructionService.reconstruct_splat` run on Objectron cup project `9522ce63dbfc454fb638fae38375863c` with `method=splatfacto`, `max_iterations=25` - wrote blocked readiness metadata and no `reconstruction/splat.ply`.
- Browser smoke at `http://127.0.0.1:5173` for viewer orientation - loaded Postshot cactus fallback and verified `Orientation: Flip Y` in large view.
- Pixel check for `data/manual-verification/cactus-orientation-flip-y-large-view.png` - nonblank canvas crop, 27,208 unique colors, 97,138 non-background pixels.
- `$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests pipeline/tests` - passed, 79 tests after orientation/readiness changes.
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts` - passed, 6 frontend helper tests after orientation/readiness changes.
- `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build` from `frontend/` with bundled Node on PATH - passed after orientation/readiness changes with chunk-size warning.

## Next step

Recommended next milestone after current work: install/verify Nerfstudio environment and run first successful `splat.ply` training.

## Real Splat Pipeline Adapter v1 notes

- Added Nerfstudio/Splatfacto runner under `pipeline/adapters/nerfstudio_splat_runner.py`.
- Added `SplatReconstructionService` and `reconstruct_splat` job type.
- Added `GET /projects/{project_id}/splat-reconstruction`.
- Added Nerfstudio configuration through `ROOMSPLAT_NERFSTUDIO_BIN_DIR`, `ROOMSPLAT_NS_PROCESS_DATA_PATH`, `ROOMSPLAT_NS_TRAIN_PATH`, and `ROOMSPLAT_NS_EXPORT_PATH`.
- Frontend Jobs panel now includes `Run splat reconstruction`, Splatfacto method selection, and max-iteration input.
- `reconstruct_splat` writes `metadata/splat_reconstruction.json` for both readiness-blocked and successful runs.
- Missing Nerfstudio dependencies produce `status: blocked_missing_dependencies`, `is_reconstruction: false`, `not_reconstruction: true`, `output_path: null`, and no fake `reconstruction/splat.ply`.
- When dependencies are ready, the adapter uses local `ns-process-data images`, `ns-train splatfacto`, and `ns-export gaussian-splat`, then copies the exported PLY to `reconstruction/splat.ply`.
- Artifact ordering now puts real `reconstruction/splat.ply` before sparse point clouds.
- Local readiness: RTX 3080 Ti visible via `nvidia-smi`; `nvcc` not on PATH; backend Python 3.12.13; `torch`, `nerfstudio`, `gsplat`, `pycolmap`, and `open3d` missing; `ns-process-data`, `ns-train`, and `ns-export` missing.
- Objectron readiness checks:
  - cup project `9522ce63dbfc454fb638fae38375863c`: 8 input frames, `blocked_missing_dependencies`, no `splat.ply`.
  - chair project `eef6d5739f524dc8a45eadc43aa0c5ec`: 14 input frames, `blocked_missing_dependencies`, no `splat.ply`.
  - shoe project `daae7b0411d54bbba2b95f71341ad5df`: 10 input frames, `blocked_missing_dependencies`, no `splat.ply`.

## Reconstruction Quality + Camera Path v1 notes

- Added COLMAP text-model parsing for `cameras.txt`, `images.txt`, and `points3D.txt` summary counts.
- `ColmapRunResult` now carries parsed camera intrinsics, registered image poses, camera centers, and trajectory bounds.
- `metadata/reconstruction.json` now includes `cameras[]`, `registered_images[]`, `camera_path[]`, `trajectory_bounds`, and preset metadata.
- Added quick/balanced/detail reconstruction presets in the UI and backend metadata. These presets currently document recommended extraction density and do not silently re-extract existing frames.
- Three.js point-cloud viewer now has toggles for points, cameras, path, grid, and axes.
- Real COLMAP point-cloud artifacts can show camera frustums and trajectory overlays from reconstruction metadata.
- Artifact ordering now prioritizes real `reconstruction/sparse-point-cloud.ply` before splats/GLB, debug frame planes, debug reports, and placeholder exports.
- Frontend helper tests cover artifact ordering; backend/pipeline tests cover parser behavior, metadata propagation, preset validation, and artifact ordering.
- Local Objectron validation with COLMAP 4.1.0 no-CUDA:
  - cup project `9522ce63dbfc454fb638fae38375863c`: 8 extracted frames, 8 registered frames, 729 PLY points, 8 cameras, inspectable.
  - chair project `eef6d5739f524dc8a45eadc43aa0c5ec`: 14 extracted frames, 14 registered frames, 3,723 PLY points, 14 cameras, inspectable.
  - shoe project `daae7b0411d54bbba2b95f71341ad5df`: 10 extracted frames, 10 registered frames, 2,041 PLY points, 10 cameras, inspectable.

## Reconstruction Quality + Camera Path v1 plan

- Saved next-goal plan at `docs/next-goals/reconstruction-quality-camera-path-v1.md`.
- Direction: parse COLMAP camera/image text outputs, store camera/path metadata, and show camera positions/frustums plus trajectory in the Three.js viewer.
- Add viewer toggles for points, cameras, path, grid, axes, and keep debug frame planes separate.
- Improve artifact ordering and placeholder/debug labeling.
- Validate against the local Objectron cup, chair, and shoe samples.

## Real Reconstruction Preview v1 plan

- Saved next-goal plan at `docs/next-goals/real-reconstruction-preview-v1.md`.
- Direction: add a local COLMAP-backed `reconstruct_point_cloud` job that produces a real sparse `point_cloud_ply` artifact from extracted frames.
- Keep Frame Room Cloud/debug frame planes explicitly labeled as not reconstruction.
- Use COLMAP dependency detection and clear setup errors instead of adding binaries, Docker, cloud upload, or paid services.
- Preserve local-only v1 assumptions and generated-data git hygiene.

## Real Reconstruction Preview v1 notes

- Added `ROOMSPLAT_COLMAP_PATH` / `COLMAP_PATH` configuration.
- Added `reconstruct_point_cloud` job type.
- Added `pipeline/adapters/colmap_sparse_runner.py` for COLMAP feature extraction, matching, mapping, TXT conversion, and PLY conversion using argument-list subprocess calls.
- Added `backend/app/services/reconstruction_jobs.py`.
- The job reads `metadata/frame_extraction.json`, validates frames stay inside the project, requires at least 3 frame images, creates a per-run workspace under `reconstruction/colmap-workspace/`, and writes `reconstruction/sparse-point-cloud.ply`.
- The job writes `metadata/reconstruction.json` with `mode: reconstruction`, `is_reconstruction: true`, `not_reconstruction: false`, registered frame count, sparse point count, PLY point count, params, COLMAP workspace, and quality notes.
- Added `GET /projects/{project_id}/reconstruction`.
- Artifact listing labels `reconstruction/sparse-point-cloud.ply` as `point_cloud_ply` with a sparse COLMAP reconstruction description.
- Frontend now exposes a `Run point cloud reconstruction` job button.
- Viewer fetches reconstruction metadata for `point_cloud_ply` artifacts and shows real reconstruction stats separately from debug frame planes.
- UI label for `debug_frame_cloud_ply` is now `Debug frame planes` to reduce confusion with real reconstruction.
- Local browser smoke used COLMAP 4.1.0 no-CUDA from ignored `data/tools/`, generated `reconstruction/sparse-point-cloud.ply`, and verified the real point-cloud viewer state.

## Nerfstudio local environment preflight notes

- Added dependency-free `.env` loading in `backend/app/config.py`; process environment variables still override `.env` values.
- Added a local ignored `.env` on this machine with `ROOMSPLAT_DATA_DIR`, `ROOMSPLAT_FFMPEG_PATH`, and `ROOMSPLAT_COLMAP_PATH`.
- Extended the Nerfstudio/Splatfacto readiness report to include FFmpeg, COLMAP, `nvidia-smi`, `nvcc`, and Visual Studio C++ compiler readiness in addition to the Nerfstudio CLIs and Python modules.
- Local audit on July 4, 2026:
  - Python available as `py -3.12`; the plain `python` alias points to the Windows Store stub in this shell.
  - GPU available: NVIDIA GeForce RTX 3080 Ti via `nvidia-smi`.
  - FFmpeg available through WinGet.
  - Local COLMAP available at `data/tools/colmap-4.1.0-nocuda/bin/colmap.exe`.
  - Visual Studio Build Tools 2022 are installed, and `cl.exe` works after calling `vcvars64.bat`.
  - CUDA Toolkit/`nvcc` is not installed or not on `PATH`.
  - `ns-process-data`, `ns-train`, and `ns-export` are not installed or not on `PATH`.
- Ran `reconstruct_splat` on Objectron cup project `9522ce63dbfc454fb638fae38375863c` with `max_iterations=25`.
- Result: `metadata/splat_reconstruction.json` was updated with `status: blocked_missing_dependencies`, `output_path: null`, and no fake `reconstruction/splat.ply`.
- Next step for real splat output: install a Windows-native isolated Nerfstudio environment with compatible PyTorch/CUDA, CUDA Toolkit/`nvcc`, and Nerfstudio CLI commands, from a Visual Studio Developer Command Prompt, then set `ROOMSPLAT_NERFSTUDIO_BIN_DIR` or the three `ROOMSPLAT_NS_*_PATH` values and rerun `reconstruct_splat`.

## Recognizable object viewer notes

- Created a new ignored local cup project from `data/sample-videos/objectron-cup-batch-3-4.MOV`.
- Extracted 53 frames at 1440x1920 and ran real COLMAP sparse reconstruction with exhaustive matching and CPU/no-GPU.
- Result: 53 registered frames and 7,535 sparse points.
- Generated `reconstruction/recognizable-cup-point-cloud.ply` as a viewer-normalized postprocess of the real sparse COLMAP point cloud:
  - color-focused magenta cup points,
  - largest connected voxel component,
  - center/scale transform for inspection,
  - 1,174 points,
  - no synthetic geometry.
- Browser verification loaded `recognizable-cup-point-cloud.ply` as `point_cloud_ply` in the Three.js viewer.
- Browser large view with grid/axes/cameras/path off showed a recognizable cup-like shape with rim/body/handle.
- Pixel check for `data/manual-verification/recognizable-cup-browser-accepted.png` found 14,738 unique colors, 26,043 non-background pixels, 7,450 object-colored pixels, and an object-colored bounding box of 349x391 px.
- Dense COLMAP was attempted on the stronger chair reconstruction, but local COLMAP reported: `Dense stereo reconstruction requires CUDA, which is not available on your system.`
- Fixed viewer camera fitting/preset bounds to use visible geometry only, so hidden camera/path overlays do not keep small artifacts zoomed out.
- This satisfies the current visual milestone as a real sparse point-cloud artifact, not as a Gaussian splat; real splat training remains blocked by missing CUDA Toolkit/`nvcc` and Nerfstudio CLI commands.

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

## 3DGS PLY sample viewer test notes

- Source sample folder: `C:\project\3DGS_PLY_sample_data`.
- Sample license/readme: CC0, with requested credit URL `https://www.steam-studio.jp`.
- Relevant formats found:
  - Postshot uncompressed PLY: Gaussian-style PLY with `x/y/z`, `f_dc_0..2`, spherical harmonic rest coefficients, opacity, scale, and rotation fields.
  - SuperSplat compressed PLY: packed chunk/sh format without normal point-cloud vertex positions.
  - RealityCapture OBJ mesh exports: useful later if we add OBJ import or convert to GLB, but not directly supported by the current browser viewer.
- Copied ignored test artifacts into local project `023ad4c91b794a0bbe6ec20f202596d7`:
  - `reconstruction/cactus-splat.ply` from Postshot uncompressed PLY, 31.4 MB, 139,410 points/splats.
  - `reconstruction/cactus-supersplat-compressed.ply` from SuperSplat compressed PLY, 8.1 MB.
- Browser verification loaded `cactus-splat.ply` in the Three.js viewer after GaussianSplats3D timed out and the point-cloud fallback took over.
- Browser large view showed a recognizable cactus-like object from the Postshot sample using mapped `f_dc_0..2` colors.
- Pixel check for `data/manual-verification/sample-cactus-postshot-fallback-large-view.png` found a nonblank crop with 22,903 unique colors.
- Browser verification for `cactus-supersplat-compressed.ply` produced a clear unsupported-format message: GaussianSplats3D timed out and point-cloud fallback failed because the PLY has no vertex positions.
- Viewer changes from this test:
  - Added a 15 second timeout around GaussianSplats3D loading so unsupported/slow splat files do not leave the UI at `Loading artifact...`.
  - Added Postshot `f_dc_0..2` mapping in PLY point fallback so Gaussian-style PLYs retain approximate color when shown as points.
  - Preserved both failure causes when splat loading and point fallback both fail.
- Current conclusion: the browser viewer can show a recognizable object from real local 3DGS sample data today, but true splat rendering for Postshot/SuperSplat variants remains a loader-compatibility milestone.

## First real RoomSplat splat goal continuation notes

- Goal achieved locally for first smoke artifact: produce and view the first real RoomSplat Gaussian splat PLY locally.
- App flow is now reaching real local tools:
  - Local micromamba 2.8.1 was installed under ignored `data/tools/micromamba`.
  - `roomsplat-nerfstudio-py310` verifies PyTorch 2.1.2+cu118, CUDA 11.8 runtime, Nerfstudio 1.1.5, and precompiled `gsplat==1.4.0+pt21cu118`.
  - `roomsplat-nerfstudio-cu124` verifies PyTorch 2.6.0+cu124, torch CUDA 12.4, gsplat 1.4.0, and Nerfstudio 1.1.5. Its compiler package is conda-forge CUDA 13.3 because conda channel resolution selected current conda-forge CUDA packages.
  - Local `.env` currently points at `roomsplat-nerfstudio-py310`.
  - Official COLMAP 3.9.1 no-CUDA is configured through `ROOMSPLAT_COLMAP_PATH` because COLMAP 4.1 renamed `SiftExtraction.use_gpu` to `FeatureExtraction.use_gpu`, while Nerfstudio 1.1.5 still sends the older flag.
- Runner hardening added during this goal:
  - `ROOMSPLAT_NERFSTUDIO_PYTHON_PATH` support for environment-specific torch/nerfstudio/gsplat readiness checks.
  - Nerfstudio subprocesses prepend isolated env paths plus configured FFmpeg/COLMAP dirs.
  - Subprocess capture uses UTF-8 with replacement to avoid Windows CP1252 crashes on Rich/Nerfstudio emoji output.
  - Visual Studio Build Tools environment is inferred for `PATH`, `INCLUDE`, and `LIB` when `cl.exe` is not already on PATH.
  - `CUDA_HOME`/`CUDA_PATH` now support both NVIDIA layout (`env\bin\nvcc.exe`) and conda-forge layout (`env\Library\bin\nvcc.exe`).
  - Nerfstudio `ns-process-data images` runs with `--no-gpu` and configured `--colmap-cmd` for local Windows COLMAP compatibility.
- Repeated `reconstruct_splat` attempts on Objectron cup project `9522ce63dbfc454fb638fae38375863c` now get through frame copying, COLMAP feature extraction/matching, dataset generation, and into `ns-train splatfacto`.
- The breakthrough was using the official precompiled `gsplat==1.4.0+pt21cu118` wheel in `roomsplat-nerfstudio-py310` instead of letting PyPI/source gsplat compile locally.
- Runner fixes required for the successful app flow:
  - `ns-train` now receives `--viewer.quit-on-train-completion True`; without it, a 1-iteration run created a checkpoint but kept the viewer/training process alive.
  - `ns-export gaussian-splat` now replaces `<config.yml>` in-place so `--output-dir` stays in the command.
- Successful run evidence:
  - Project: `9522ce63dbfc454fb638fae38375863c` / Objectron cup extraction smoke.
  - `SplatReconstructionService.reconstruct_splat(..., method='splatfacto', max_iterations=1)` returned `status: succeeded`.
  - `data/9522ce63dbfc454fb638fae38375863c/reconstruction/splat.ply` exists, 197,014 bytes.
  - PLY header: `format binary_little_endian 1.0`, `comment Generated by Nerstudio 1.1.5`, `element vertex 788`.
  - `metadata/splat_reconstruction.json` records `is_reconstruction: true`, `not_reconstruction: false`, `output_path: reconstruction/splat.ply`, and `command_count: 3`.
- Browser viewer evidence:
  - `splat.ply` is listed first as `Splat PLY`.
  - Large-view browser smoke loaded the artifact as `splat_ply` fallback with 781 points.
  - Screenshot: ignored `data/manual-verification/first-real-roomsplat-splat-large-view.png`.
  - Pixel check: 1210x610 screenshot, 4,450 unique colors, 14,791 non-background pixels, 1,520 colored pixels.
- Remaining viewer limitation:
  - GaussianSplats3D still times out on the Nerfstudio PLY and the UI displays the file through point-cloud fallback with an explicit warning. This is now a browser loader compatibility issue, not a reconstruction/export blocker.
- Historical failures before precompiled gsplat:
  - CUDA 11.8 env: MSVC/STL compatibility failures and CUB compile errors with current VS 2022 Build Tools.
  - CUDA 13.3 compiler + PyTorch cu124 env: CCCL/MSVC traditional preprocessor guard remains unless the gsplat/PyTorch build passes `/Zc:preprocessor` or suppresses `CCCL_IGNORE_MSVC_TRADITIONAL_PREPROCESSOR_WARNING` at the actual `nvcc` host compiler invocation.
  - A final 1-iteration smoke run timed out after 15 minutes during gsplat build/training and produced no `reconstruction/splat.ply`.
- Validation after this cleanup:
  - `$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests pipeline/tests` - passed, 84 tests after first real splat success.
  - Bundled Node frontend helper tests - passed, 6 tests.
  - Bundled Node Vite build from `frontend/` - passed with the existing large chunk warning.
- Viewer now includes Orientation presets: Source, Flip X/Y/Z, Z-up to Y-up, and Y-up to Z-up.
- Browser verification loaded the Postshot cactus sample as `splat_ply` fallback and used `Flip Y` to inspect it upright in large view.
- Screenshot saved to ignored `data/manual-verification/cactus-orientation-flip-y-large-view.png`.

## First recognizable RoomSplat splat continuation notes

- Added viewer-side robust/focused fitting for point-based artifacts so outliers do not always dominate the camera.
- Added a Gaussian PLY fallback that maps Nerfstudio `f_dc_*`, `opacity`, and `scale_*` properties to scaled alpha point sprites when GaussianSplats3D times out.
- Restored GaussianSplats3D timeout to 15 seconds; Nerfstudio PLYs still fall back instead of native splat rendering.
- Verified existing RoomSplat splats in the browser:
  - Objectron cup, 53 frames, 1000 Splatfacto iterations, 12,412 splat vertices, 2.9 MB: not recognizable.
  - Objectron chair, 60 frames, 1000 Splatfacto iterations, 44,601 splat vertices, 10.6 MB: partially suggestive but not confidently recognizable.
- Generated and verified a new Objectron shoe splat:
  - 10 frames, 1000 Splatfacto iterations, 12,255 splat vertices, 3.0 MB.
  - 10 frames, 3000 Splatfacto iterations, 165,962 splat vertices, 41.2 MB.
- Best current screenshot: ignored `data/manual-verification/recognizable-splat-shoe-3000-gaussian-fallback-large-view.png`.
- Current assessment: shoe 3000 is the best candidate and has a rough shoe/sole-like region, but the active goal is not yet complete because the object is still too noisy to call robustly recognizable.
- Frontend helper tests passed with 12 tests and Vite build passed with the existing chunk-size warning after these viewer changes.
- Next likely step: improve native Nerfstudio Gaussian PLY rendering compatibility or improve reconstruction input/masking; viewer-only camera controls are no longer the main bottleneck.
- Created a local ignored masked-chair project from the existing Objectron chair frames:
  - Project `a2e709418e654a6ca6319bf21e4ef231`, `Objectron chair masked orange 60 frames`.
  - Input prep: 60 existing chair frames, downscaled to 720x960, with background damped outside the orange chair silhouette.
  - Splatfacto 1000 iterations completed in 173.71 seconds.
  - Output `reconstruction/splat.ply` is a real Nerfstudio PLY, 7,239,472 bytes, 29,185 vertices.
  - Metadata reports `status: succeeded`, `is_reconstruction: true`, and `output_path: reconstruction/splat.ply`.
- Browser verification loaded the masked-chair artifact as `splat_ply`; GaussianSplats3D native rendering still timed out, then the Gaussian PLY fallback displayed it as scaled alpha sprites.
- Manual screenshot: ignored `data/manual-verification/recognizable-splat-chair-masked-1000-gaussian-fallback-large-view.png`.
- Pixel check for the masked-chair screenshot: 598x830, 31,085 unique colors, 53,132 non-background pixels, 5,690 orange pixels, orange bbox 230x212 px.
- Current assessment: this satisfies the first recognizable RoomSplat splat goal as a recognizable orange bowl-chair object from a real local Nerfstudio/Splatfacto reconstruction, with the limitation that browser native splat rendering still falls back.

## Milestone 10 learned geometry import/preflight notes

- Inspected local reference copy `C:\project\lingbot-map` for practical output-shape inspiration.
- Useful LingBot/BSS-inspired shape:
  - `.complete.json` with `metadata.frame_keys`, `metadata.global_keys`, and optional `metadata.frame_index_map`.
  - Global `points.ply`.
  - `traj.txt` camera-to-world rows.
  - `intrinsics.txt` rows with `fx`, `fy`, `cx`, `cy`, `width`, `height`.
  - `sampling.json`.
  - Per-frame `depth/`, `confidence/`, `mask/`, and `points/` sidecar folders.
- Added `pipeline/adapters/learned_geometry_import.py` with source-folder inspection, expected sidecars, and import assessment helpers.
- Added backend `LearnedGeometryImportService`.
- Added job types:
  - `learned_geometry_preflight`
  - `import_learned_geometry`
- `learned_geometry_preflight` validates extracted project frames, source completion metadata, primary PLY, source-contained sidecars, frame mapping, and output contract without copying files.
- `import_learned_geometry` copies the primary PLY to `reconstruction/learned-point-cloud.ply`, copies known sidecars under `metadata/learned/<adapter-slug>/`, writes `metadata/geometry_bundle.json`, and then validates the completed bundle.
- Imported primary PLYs are labeled `predicted_point_cloud_ply` only after the geometry bundle validates.
- Imported learned geometry remains `is_reconstruction: false` and `not_reconstruction: true`.
- Frontend Jobs panel now supports learned geometry source folder, adapter label, primary PLY, preflight, and import.
- Frontend Viewer panel displays `learned_geometry_bundle` as metadata/JSON inspection while `predicted_point_cloud_ply` continues to use the Three.js point viewer warning path.
- Added focused tests:
  - backend learned geometry preflight/import success;
  - missing extracted frames;
  - missing primary PLY;
  - escaped source-relative primary path;
  - missing declared sidecar folder;
  - out-of-range frame map;
  - pipeline source inspection and sidecar expectation helpers;
  - frontend bundle summary/job type helpers.
- Validation:
  - `$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests pipeline/tests` - passed, 108 tests.
  - Bundled Node frontend helper tests - passed, 12 tests.
  - Bundled Node Vite build from `frontend/` - passed with the existing large chunk warning.
  - `git diff --check` - passed with line-ending warnings only.
- No LingBot-Map runtime, VGGT runtime, checkpoint loader, automatic model download, cloud dependency, or required learned runtime was added.
- Remaining future work:
  - Add an optional isolated learned runtime adapter only after checkpoint/checksum/allowlist and no-auto-download policy is designed.
  - Add direct readers/filters for depth, confidence, and pointmap sidecars in the browser viewer.
  - Add size/file-count limits for very large learned sidecar folders before using this with long videos.

## Milestone 9 learned geometry readiness notes

- Added `metadata/geometry_bundle.json` as the first RoomSplat-native learned geometry bundle contract.
- Added backend Pydantic validation for schema version, source adapter, frame mapping, cameras, intrinsics, trajectory, depth/confidence/mask/pointmap capabilities, primary artifacts, sidecars, quality notes, warnings, generated-data rules, completion status, and path containment.
- Added a pipeline-side learned geometry adapter contract helper so future learned adapters declare the same `metadata/geometry_bundle.json` and `predicted_point_cloud_ply` boundary before any runtime integration.
- Added `GET /projects/{project_id}/geometry-bundle`.
- Added artifact labels:
  - `predicted_point_cloud_ply` for bundle-declared learned/predicted PLY outputs.
  - `learned_geometry_bundle` for validated bundle metadata.
- Invalid or incomplete geometry bundles are not listed and do not promote their declared PLY outputs; this prevents learned/predicted outputs from silently falling back to generic `point_cloud_ply`.
- Learned geometry bundles must report `is_reconstruction: false` and `not_reconstruction: true` until a future adapter explicitly promotes or converts them into verified reconstruction artifacts.
- Frontend API/types and viewer helpers now understand predicted point-cloud PLY and learned geometry bundle metadata.
- Three.js viewer can load `predicted_point_cloud_ply` through the point-cloud path with an explicit learned/predicted geometry warning.
- No LingBot-Map, VGGT, checkpoint loader, automatic download, or learned-model runtime dependency was added.
- Remaining future work:
  - Add an actual optional learned adapter after checkpoint safety and isolated runtime rules are finalized.
  - Add richer viewer controls for confidence filtering, current/all-frame mode, frame selection, clickable learned cameras/frustums, and camera downsampling.
  - Add depth/confidence sidecar readers only after storage size limits and UI behavior are designed.

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
