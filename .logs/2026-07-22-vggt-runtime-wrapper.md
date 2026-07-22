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

## Follow-up: first real local VGGT smoke

The first real local VGGT smoke was run on the Windows RTX 3080 Ti machine.

Local setup:

- Cloned VGGT into ignored `data/tools/vggt`.
- Installed VGGT editable into `data/tools/micromamba-root/envs/roomsplat-nerfstudio-py310`.
- Installed local runtime helpers: `safetensors`, `huggingface_hub`, `einops`, and `opencv-python`.
- Pinned `numpy==1.26.4` after `opencv-python` temporarily pulled in NumPy 2.x, which conflicts with VGGT's `numpy<2` requirement.
- Downloaded `facebook/VGGT-1B` `model.pt` manually into ignored `data/models/vggt/model.pt`.
- Checkpoint SHA-256: `D15BF50A8615C8225ED48B51EA5CAC673D82442EC0309036DF555A053253AFE0`.
- Updated ignored local `.env` with the VGGT Python command, absolute wrapper path, model root, checkpoint path/SHA, cache dir, 7 GB minimum free VRAM, and 30 minute timeout.

Smoke settings:

- Project: `9522ce63dbfc454fb638fae38375863c` (`Objectron cup extraction smoke`).
- Adapter: `vggt`.
- `max_frames=4`.
- `frame_step=1`.
- `image_max_size=518`.
- `precision=fp16`.
- `allow_cpu_offload=false`.

Result:

- Preflight passed as `ready`.
- Observed GPU: NVIDIA GeForce RTX 3080 Ti, 12,288 MB total VRAM, 8,904 MB free.
- Estimated required VRAM: 6,481 MB.
- Smoke job `9eca3bc933234337902ac6e675279143` succeeded.
- Runtime returned `command_returncode=0`.
- Imported `reconstruction/learned-point-cloud.ply` as `predicted_point_cloud_ply`.
- PLY header reports `element vertex 100000`.
- `metadata/geometry_bundle.json` now records that the output came from a local SHA-256 allowlisted checkpoint and keeps `not_reconstruction: true`.
- Browser verification at `http://127.0.0.1:5173/` selected `learned-point-cloud.ply`; the Three.js viewer reported `Points: 100,000` and rendered a nonblank predicted point-cloud view.

Code follow-up:

- `pipeline/scripts/run_vggt_runtime.py` now uses `datetime.now(timezone.utc)` instead of Python 3.11+ `datetime.UTC`, because the current VGGT env is Python 3.10.
- `LearnedRuntimeService` annotates imported runtime geometry bundles so successful model runs do not retain the generic "No model checkpoint was loaded" import warning.

Remaining work:

- Increase the smoke budget gradually from 4 frames toward 8-12 frames.
- Compare viewer quality before raising `image_max_size`.
- Tune point filtering/orientation/normalization after the viewer output is visually inspected.
