# Real Reconstruction Preview v1

## Summary

Implemented the first COLMAP-backed sparse point-cloud reconstruction path and tightened debug frame plane labeling so the debug viewer artifact is less likely to be mistaken for real reconstruction.

## Changes

- Added COLMAP executable configuration:
  - `ROOMSPLAT_COLMAP_PATH`
  - `COLMAP_PATH`
- Added job type:
  - `reconstruct_point_cloud`
- Added pipeline runner:
  - `pipeline/adapters/colmap_sparse_runner.py`
- Added backend service:
  - `backend/app/services/reconstruction_jobs.py`
- Added metadata endpoint:
  - `GET /projects/{project_id}/reconstruction`
- Added output contract:
  - `reconstruction/sparse-point-cloud.ply`
  - `metadata/reconstruction.json`
- Updated frontend job controls and viewer metadata display.
- Renamed current debug artifact label in the UI from `Frame Room Cloud` to `Debug frame planes`.

## Security and Filesystem Notes

- COLMAP commands are built as argument lists and executed with `shell=False`.
- Frame, workspace, metadata, and output paths are resolved under the project directory.
- A per-run COLMAP workspace is created under `reconstruction/colmap-workspace/`.
- Generated reconstruction data remains under ignored project data directories.
- Missing COLMAP fails with an actionable dependency message instead of writing placeholder output.

## Validation

- Focused backend/pipeline tests passed:
  - `backend/tests/test_jobs.py`
  - `backend/tests/test_artifacts.py`
  - `pipeline/tests/test_colmap_sparse_runner.py`
- Frontend helper tests passed.
- Frontend build passed with the known large chunk warning from Three.js/GaussianSplats3D.
- Final full backend/pipeline suite passed:
  - 62 tests
- Final frontend helper suite passed:
  - 4 tests
- Final audit passed:
  - 0 vulnerabilities
- Final `git diff --check` passed with line-ending warnings only.
- Direct service run against Objectron project passed:
  - 8 input frames
  - 8 registered frames
  - 729 sparse/PLY points
- Browser UI job run passed:
  - job type `reconstruct_point_cloud`
  - status `succeeded`
  - 8 registered frames
  - 731 sparse/PLY points
- Browser viewer verification passed:
  - `sparse-point-cloud.ply` listed as `point_cloud_ply`
  - reconstruction metadata stats visible
  - real COLMAP notice visible
  - debug frame planes not-reconstruction warning visible
  - artifact switching works
  - fit/reset/point-size/color controls respond
- Browser screenshot saved:
  - `data/manual-verification/real-reconstruction-preview-v1.png`
- Canvas pixel check:
  - nonblank canvas crop
  - 1,892 unique colors
  - non-background ratio 0.044931

## Environment Finding

- `colmap.exe` was not found on PATH in the current shell.
- `ROOMSPLAT_COLMAP_PATH` was not set.
- `winget search COLMAP` found no package.
- Official COLMAP 4.1.0 no-CUDA Windows release asset was downloaded into ignored `data/tools/`.
- Smoke tests used:
  - `C:\project\RoomSplat\data\tools\colmap-4.1.0-nocuda\bin\colmap.exe`

## Remaining Work

- Commit and push only after validation is complete.
