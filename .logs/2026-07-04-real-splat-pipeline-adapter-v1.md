# Real Splat Pipeline Exploration + First Local Splat Adapter v1

## Summary

Added the first local Gaussian splat adapter boundary for RoomSplat. The selected path is Nerfstudio/Splatfacto because it is the mature local training route already aligned with the project direction.

The current machine is not ready to train because Nerfstudio/PyTorch/gsplat CLI dependencies are missing, so this milestone implements a diagnosable `reconstruct_splat` flow instead of writing fake splat output.

## Local readiness

- Python: 3.12.13 in the bundled Codex runtime.
- GPU: NVIDIA GeForce RTX 3080 Ti visible through `nvidia-smi`.
- NVIDIA driver reports CUDA UMD support, but `nvcc` is not on PATH.
- Missing backend Python modules: `torch`, `nerfstudio`, `gsplat`, `pycolmap`, `open3d`.
- Missing CLIs on PATH: `ns-process-data`, `ns-train`, `ns-export`.
- `colmap.exe` is not on PATH, but ignored local COLMAP 4.1.0 no-CUDA exists under `data/tools/`.

## Implementation

- Added `pipeline/adapters/nerfstudio_splat_runner.py`.
- Added `backend/app/services/splat_reconstruction.py`.
- Added `reconstruct_splat` job type.
- Added `GET /projects/{project_id}/splat-reconstruction`.
- Added Nerfstudio CLI configuration through:
  - `ROOMSPLAT_NERFSTUDIO_BIN_DIR`
  - `ROOMSPLAT_NS_PROCESS_DATA_PATH`
  - `ROOMSPLAT_NS_TRAIN_PATH`
  - `ROOMSPLAT_NS_EXPORT_PATH`
- Frontend Jobs panel now has `Run splat reconstruction`, method selection, and max-iteration input.
- Artifact ordering now puts real `reconstruction/splat.ply` ahead of sparse point clouds.

## Objectron validation

Readiness checks used `method=splatfacto`, `max_iterations=3000`.

| Sample | Project | Input frames | Status | Output |
|---|---|---:|---|---|
| cup | `9522ce63dbfc454fb638fae38375863c` | 8 | blocked_missing_dependencies | no `splat.ply` |
| chair | `eef6d5739f524dc8a45eadc43aa0c5ec` | 14 | blocked_missing_dependencies | no `splat.ply` |
| shoe | `daae7b0411d54bbba2b95f71341ad5df` | 10 | blocked_missing_dependencies | no `splat.ply` |

## Validation so far

- `python -m pytest pipeline/tests/test_nerfstudio_splat_runner.py backend/tests/test_jobs.py backend/tests/test_artifacts.py` - passed, 40 tests.
- `node --experimental-strip-types --test frontend/tests/*.test.ts` - passed, 5 tests.
- `node node_modules/vite/bin/vite.js build` from `frontend/` - passed with existing large chunk warning.
- Browser smoke at `http://127.0.0.1:5173` - passed after backend restart. The UI showed `Run splat reconstruction`, created a `reconstruct_splat` job, displayed `blocked_missing_dependencies`, did not show `[object Object]`, and did not list `splat.ply`.
- Filesystem check confirmed `data/9522ce63dbfc454fb638fae38375863c/reconstruction/splat.ply` does not exist while `metadata/splat_reconstruction.json` reports `status: blocked_missing_dependencies`, `is_reconstruction: false`, `not_reconstruction: true`, and `output_path: null`.
- `python -m pytest backend/tests pipeline/tests` - passed, 76 tests.
- `node --experimental-strip-types --test frontend/tests/*.test.ts` - passed, 5 tests.
- `node node_modules/vite/bin/vite.js build` from `frontend/` - passed with existing large chunk warning.
- `pnpm dlx npm@latest --prefix frontend audit --audit-level=moderate` - passed, 0 vulnerabilities.

## References checked

- Nerfstudio installation docs: https://docs.nerf.studio/quickstart/installation.html
- Nerfstudio custom data docs: https://docs.nerf.studio/quickstart/custom_dataset.html
- Nerfstudio Splatfacto docs: https://docs.nerf.studio/nerfology/methods/splat.html
- gsplat Windows install notes: https://github.com/nerfstudio-project/gsplat/blob/main/docs/INSTALL_WIN.md

## Remaining risks

- Real training still depends on installing a compatible Nerfstudio/PyTorch/CUDA/Build Tools environment.
- Current adapter uses the official Nerfstudio CLI flow instead of directly reusing the existing COLMAP sparse workspace; this is the least brittle first path.
- Future work may add a conversion path from existing COLMAP outputs to Nerfstudio data if it proves stable.
