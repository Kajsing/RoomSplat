# Reconstruction Quality + Camera Path v1

## Summary

Implemented camera/path metadata for COLMAP sparse reconstruction and added viewer controls for inspecting real point clouds with camera frustums and trajectory overlays.

## Changes

- Parsed COLMAP `cameras.txt` and `images.txt` from the converted TXT model.
- Calculated registered image camera centers from COLMAP `qvec`/`tvec`.
- Added trajectory bounds and ordered camera path records to `metadata/reconstruction.json`.
- Added quick/balanced/detail reconstruction presets. The presets are recorded as run guidance and do not silently re-extract existing frames.
- Added Three.js toggles for points, cameras, path, grid, and axes.
- Added camera frustum and trajectory overlays for real `point_cloud_ply` artifacts when reconstruction metadata exists.
- Sorted artifacts so real sparse point clouds appear before debug frame planes, debug reports, and placeholder exports.
- Added focused parser, metadata, preset, artifact ordering, and frontend helper tests.

## Local Objectron validation

COLMAP: `data/tools/colmap-4.1.0-nocuda/bin/colmap.exe`

Params: `preset=balanced`, `matcher=exhaustive`, `use_gpu=false`

| Sample | Project | Extracted frames | Registered frames | PLY points | Cameras | Quality |
|---|---|---:|---:|---:|---:|---|
| cup | `9522ce63dbfc454fb638fae38375863c` | 8 | 8 | 729 | 8 | inspectable |
| chair | `eef6d5739f524dc8a45eadc43aa0c5ec` | 14 | 14 | 3,723 | 14 | inspectable |
| shoe | `daae7b0411d54bbba2b95f71341ad5df` | 10 | 10 | 2,041 | 10 | inspectable |

## Validation so far

- `python -m pytest pipeline/tests/test_colmap_sparse_runner.py backend/tests/test_jobs.py backend/tests/test_artifacts.py` - passed, 39 tests.
- `node --experimental-strip-types --test frontend/tests/*.test.ts` - passed, 5 tests.
- `node node_modules/vite/bin/vite.js build` from `frontend/` - passed with the existing large chunk warning.
- Browser smoke at `http://127.0.0.1:5173` - passed with Objectron cup project. Viewer selected `sparse-point-cloud.ply`, showed 729 points, 8 cameras, 8 path points, 8 registered frames, and 729 sparse points.
- Browser toggles for points, cameras, path, grid, and axes were switched off/on and ended checked.
- Canvas screenshot saved to ignored `data/manual-verification/reconstruction-quality-camera-path-v1.png`.
- Canvas pixel check: 844x475 crop, 3,857 unique colors, 23,654 non-background pixels, ratio 0.059002.
- `python -m pytest backend/tests pipeline/tests` - passed, 67 tests.
- `node --experimental-strip-types --test frontend/tests/*.test.ts` - passed, 5 tests.
- `node node_modules/vite/bin/vite.js build` from `frontend/` - passed with the existing large chunk warning.
- `pnpm dlx npm@latest --prefix frontend audit --audit-level=moderate` - passed, 0 vulnerabilities.

## Assumptions

- COLMAP TXT model format follows the standard paired `images.txt` image/points2D lines.
- Camera frustums are debug/inspection overlays, not measurement-grade camera geometry.
- quick/balanced/detail presets guide extraction density and are recorded with the run; changing already extracted frames remains an explicit user action.

## Remaining risks

- Sparse COLMAP point clouds are still conventional point geometry, not Gaussian splat reconstruction.
- Very large future point clouds may need viewer-level streaming or decimation.
- Real Gaussian Splatting training remains future work; this milestone improves sparse point-cloud inspection and camera/path understanding.
