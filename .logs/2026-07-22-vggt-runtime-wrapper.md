# VGGT runtime wrapper

## Goal

Implement the first concrete learned-model adapter wrapper for RoomSplat, using VGGT as the first target while keeping checkpoint acquisition manual and local-only.

## Sources

- VGGT GitHub: https://github.com/facebookresearch/vggt
- VGGT model card: https://huggingface.co/facebook/VGGT-1B
- Commercial checkpoint note: https://huggingface.co/facebook/VGGT-1B-Commercial

VGGT predicts camera parameters, depth maps, point maps, and tracks from one or more views. RoomSplat uses the wrapper first to produce predicted point-cloud geometry for inspection through the existing geometry bundle path.

## Implementation

- Added `pipeline/scripts/run_vggt_runtime.py`.
- The script implements the Milestone 11 runtime command contract:
  - `--frames-dir`
  - `--output-dir`
  - `--checkpoint`
  - `--max-frames`
  - `--image-max-size`
  - `--precision`
  - `--frame-index-map`
  - optional `--allow-cpu-offload`
- Added optional wrapper flags:
  - `--device`
  - `--max-points`
  - `--confidence-threshold`
  - `--dry-run`
- Successful inference writes:
  - `.complete.json`
  - `points.ply`
  - `sampling.json`
  - `traj.txt` when camera predictions are available
  - `intrinsics.txt` when camera predictions are available
- Output is designed to be imported by the existing `LearnedGeometryImportService`.
- Frontend learned runtime adapter default now points at `vggt`.
- Added `docs/vggt-runtime.md`.

## Local state

- `nvidia-smi` reports NVIDIA GeForce RTX 3080 Ti, 12,288 MB total VRAM, 8,878 MB free during this slice.
- Existing Nerfstudio micromamba envs contain `torch`, `torchvision`, and `numpy`.
- Existing envs do not contain `vggt`, `safetensors`, or `huggingface_hub`.
- No VGGT checkpoint was found under `data/models`.
- Real VGGT inference was not run because dependencies/checkpoint were not present and checkpoint download must remain manual.

## Safety validation

- `pipeline/scripts/run_vggt_runtime.py --help` works.
- Wrapper dry-run writes `blocked_vggt_runtime.json` and does not write `.complete.json` or `points.ply`.
- Direct `learned_runtime_smoke` with the VGGT wrapper command configured but no checkpoint returned:
  - `status: blocked_missing_checkpoint`
  - `output_path: null`
  - no `metadata/geometry_bundle.json`
  - no `reconstruction/learned-point-cloud.ply`

## Remaining work

- Manually install/configure a VGGT runtime environment.
- Manually place the chosen checkpoint under `data/models/vggt/`.
- Compute and set `ROOMSPLAT_LEARNED_CHECKPOINT_SHA256`.
- Run real 8-12 frame VGGT smoke through `learned_runtime_preflight` and `learned_runtime_smoke`.
