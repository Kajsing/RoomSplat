# 2026-07-04 first real splat goal continuation

## Scope

- Continued the active goal: produce and view the first real RoomSplat Gaussian splat locally.
- Verified current Nerfstudio/Splatfacto readiness from the current machine state.
- Added viewer orientation presets needed for imported splat/PLY artifacts that appear upside down or use a different up axis.

## Current readiness evidence

- `ns-process-data`, `ns-train`, and `ns-export` are not on PATH.
- `conda` is not on PATH.
- CUDA Toolkit/`nvcc` is not on PATH.
- `nvidia-smi` is available at `C:\Windows\System32\nvidia-smi.exe`.
- Visual Studio Build Tools are discoverable via `vcvars64.bat`.
- FFmpeg is available and local COLMAP is configured.
- Upstream Nerfstudio Windows guidance still points to an isolated conda environment, Visual Studio C++ activation, PyTorch CUDA, CUDA toolkit, then Nerfstudio install/verification.
- Splatfacto uses `gsplat`, benefits from COLMAP/`ns-process-data` initialization, and exports splats with `ns-export gaussian-splat`.

## Splat job run

- Ran `SplatReconstructionService.reconstruct_splat` directly on Objectron cup project `9522ce63dbfc454fb638fae38375863c`.
- Params: `method=splatfacto`, `max_iterations=25`.
- Result: `metadata/splat_reconstruction.json` has `status: blocked_missing_dependencies`, `is_reconstruction: false`, `output_path: null`.
- Confirmed `reconstruction/splat.ply` does not exist.
- This is not goal completion; it is the correct no-fake-output readiness state.

## Changes

- Added viewer orientation presets:
  - Source
  - Flip X
  - Flip Y
  - Flip Z
  - Z-up to Y-up
  - Y-up to Z-up
- Orientation transforms apply to the artifact root without reloading large PLY files.
- Added frontend helper coverage for orientation preset labels.
- Added `backend-python` and optional `conda` entries to Nerfstudio readiness diagnostics.
- Updated docs for the current real-splat blocker and the new orientation control.

## Browser verification

- Loaded local cactus `splat_ply` sample in the browser viewer through point-cloud fallback.
- Selected `Orientation: Flip Y`.
- Opened large view and verified the cactus appears upright.
- Screenshot saved under ignored `data/manual-verification/cactus-orientation-flip-y-large-view.png`.
- Pixel check on canvas crop: 27,208 unique colors and 97,138 non-background pixels.

## Validation

- Backend/pipeline tests passed: 79 tests.
- Frontend helper tests passed: 6 tests.
- Frontend build passed with the known chunk-size warning.

## Remaining

- Install or connect a Windows-native isolated Nerfstudio environment.
- Verify `ns-process-data --help`, `ns-train splatfacto --help`, and `ns-export gaussian-splat --help`.
- Set `ROOMSPLAT_NERFSTUDIO_BIN_DIR` or individual `ROOMSPLAT_NS_*_PATH` values.
- Rerun `reconstruct_splat` and verify real `reconstruction/splat.ply` in the browser viewer.
