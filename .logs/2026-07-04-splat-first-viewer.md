# Splat-first browser viewer

Date: 2026-07-04

Goal: implement a real browser-based Three.js viewer with splat-first direction and a debug Frame Room Cloud artifact generated from extracted frames.

## Completed

- Added frontend dependencies `three` and `@mkkellogg/gaussian-splats-3d`.
- Upgraded Vite after npm audit reported Windows/dev-server advisories in the previous Vite version.
- Added backend job type `debug_frame_cloud`.
- Added `debug_frame_cloud_ply` artifact type.
- Added deterministic Frame Room Cloud generation from `metadata/frame_extraction.json` and sampled frame images.
- Frame Room Cloud writes:
  - `reconstruction/debug-frame-room.ply`
  - `metadata/debug_frame_cloud.json`
- Metadata marks the artifact as `mode: debug` and `not_reconstruction: true`.
- Added `GET /projects/{project_id}/frames/extraction` so the frontend can detect existing extracted frames.
- Replaced the old 2D canvas PLY preview with `ThreeViewer`.
- Viewer supports debug frame cloud PLY, point cloud PLY, splat PLY fallback, GLB scene loading, and debug report switching.
- Manual browser smoke used the Objectron cup project and saved ignored screenshot output under `data/manual-verification/viewer-smoke.png`.

## Security and correctness notes

- Frame Room Cloud never claims to be reconstruction.
- Generator resolves frame metadata and frame paths under the project directory.
- Output remains under `reconstruction/` and metadata remains under `metadata/`.
- Generated PLY/PNG/browser smoke artifacts stay under ignored `data/`.
- `npm audit` is clean after the Vite upgrade.

## Validation so far

- Focused backend tests passed: `backend/tests/test_video_import.py backend/tests/test_jobs.py backend/tests/test_artifacts.py`.
- Frontend build passed with a chunk-size warning caused by Three.js/viewer assets.
- Browser smoke passed:
  - Debug frame cloud job generated 46,464 points.
  - Artifact list labeled it `debug_frame_cloud_ply`.
  - Three.js canvas was nonblank with 3,363 unique colors in the canvas crop.
  - Grid/axes toggles, color mode, point size, reset, fit, artifact switching, and orbit/zoom interaction were exercised.

## Remaining risks

- Real Gaussian Splatting reconstruction is still not integrated.
- Splat PLY support depends on whether GaussianSplats3D can parse the concrete PLY emitted by a future reconstruction adapter.
- GLB rendering works for scene artifacts, but real conversion/export quality depends on future pipeline work.
- Vite reports a large client chunk; acceptable for this local milestone, but future viewer code-splitting may be useful.
