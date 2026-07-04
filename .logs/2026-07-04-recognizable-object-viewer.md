# Recognizable object viewer run

Date: 2026-07-04

## Goal

Continue RoomSplat until a recognizable real object is visible in the browser viewer.

## Nerfstudio/Splatfacto status

- `ns-train` is still not available on `PATH`.
- CUDA Toolkit/`nvcc` is still not available on `PATH`.
- GPU driver is available through `nvidia-smi` for NVIDIA GeForce RTX 3080 Ti.
- Real Gaussian splat training remains blocked on local CUDA Toolkit + Nerfstudio CLI setup.

## Reconstruction attempts

### Chair

- Created ignored local project `ee74273c8742486ba4222acf52d493e6` named `Objectron chair recognition 60 frames`.
- Imported `data/sample-videos/objectron-chair-batch-43-5.MOV`.
- Extracted 60 frames at 1440x1920.
- Ran COLMAP sparse reconstruction with exhaustive matcher, CPU/no-GPU.
- Result: 60 registered frames, 22,687 sparse points.
- Dense COLMAP attempt failed because the local COLMAP no-CUDA build reports: `Dense stereo reconstruction requires CUDA, which is not available on your system.`
- Generated a focused chair point-cloud crop from the largest connected voxel component for inspection; it was better than the raw sparse cloud but not clearly recognizable enough.

### Cup

- Created ignored local project `33c4f34d780f49e6ad64bcf31364e241` named `Objectron cup recognition 53 frames`.
- Imported `data/sample-videos/objectron-cup-batch-3-4.MOV`.
- Extracted 53 frames at 1440x1920.
- Ran COLMAP sparse reconstruction with exhaustive matcher, CPU/no-GPU.
- Result: 53 registered frames, 7,535 sparse points.
- Generated `reconstruction/recognizable-cup-point-cloud.ply` from the real sparse COLMAP cloud:
  - magenta color threshold,
  - largest connected voxel component,
  - center/scale transform for viewer inspection,
  - 1,174 output points,
  - no synthetic geometry.

## Viewer work

- Found that the viewer fit/preset logic could include hidden or irrelevant scene geometry while computing bounds.
- Updated `ThreeViewer` to compute camera fit bounds from visible geometry only.
- Browser loaded `recognizable-cup-point-cloud.ply` as `point_cloud_ply`.
- Large view with overlays off showed a recognizable cup-like point cloud with bowl/rim and handle shape.
- Screenshot saved under ignored generated data:
  - `data/manual-verification/recognizable-cup-browser-accepted.png`
- Pixel check saved under ignored generated data:
  - `data/manual-verification/recognizable-cup-browser-pixel-check.json`
- Pixel check result:
  - screenshot: 1186x667,
  - unique colors: 14,738,
  - non-background pixels: 26,043,
  - object-colored pixels: 7,450,
  - object box: 349x391 px.

## Remaining risks

- This is still a sparse point-cloud recognition result, not a Gaussian splat.
- The recognizable cup artifact is a viewer-normalized postprocess of real COLMAP points; it should be described as a focused point cloud, not a splat or dense reconstruction.
- Dense COLMAP and Nerfstudio splat training still need CUDA Toolkit/`nvcc`.

## Validation

- `py -3.12 -m pytest backend/tests pipeline/tests`
- Result: passed, 79 tests.
- Bundled Node Vite build from `frontend/`: `node node_modules/vite/bin/vite.js build`
- Result: passed with the known large chunk warning for viewer dependencies.
- `git diff --check`
- Result: passed with Git line-ending warnings only.
