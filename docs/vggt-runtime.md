# VGGT Runtime Wrapper

RoomSplat's first concrete learned-model adapter target is VGGT.

Primary references:

- VGGT GitHub: https://github.com/facebookresearch/vggt
- VGGT model card: https://huggingface.co/facebook/VGGT-1B
- VGGT commercial checkpoint note: https://huggingface.co/facebook/VGGT-1B-Commercial

VGGT predicts camera parameters, depth maps, point maps, and tracks from one or more scene views. RoomSplat uses it first as a feed-forward predicted point-cloud source, not as a verified metric scanner and not as Gaussian splat output.

## Local-only policy

- RoomSplat does not download VGGT code or checkpoints automatically.
- The wrapper loads only the checkpoint path passed by the Milestone 11 runtime service.
- The checkpoint must live under `ROOMSPLAT_LEARNED_MODEL_ROOT`.
- `ROOMSPLAT_LEARNED_CHECKPOINT_SHA256` must match before `learned_runtime_smoke` is considered ready.
- Checkpoints, caches, selected frames, and runtime outputs stay in ignored local data folders.
- Do not expose the backend beyond `127.0.0.1`; v1 has no authentication.

## Suggested local layout

```text
C:\project\RoomSplat\
  data\
    models\
      vggt\
        model.pt
    cache\
      learned-runtime\
  pipeline\
    scripts\
      run_vggt_runtime.py
```

The original `facebook/VGGT-1B` model card currently identifies a 1B-parameter F32 checkpoint under a non-commercial license. A separate commercial-use checkpoint exists behind an approval flow. Choose the checkpoint that matches your intended use.

Expected local storage:

- Checkpoint file: about 5 GB.
- Practical disk/cache headroom: at least 10-20 GB while experimenting.
- VRAM: start with a 12 GB GPU smoke budget only. A 5 GB checkpoint can need substantially more than 5 GB VRAM during inference because frame count, resolution, activations, precision, and CUDA/PyTorch overhead matter.

## Configure

Example `.env` entries after manually installing a VGGT environment and placing the checkpoint locally:

```text
ROOMSPLAT_LEARNED_RUNTIME_COMMAND=C:\path\to\vggt-env\python.exe
ROOMSPLAT_LEARNED_RUNTIME_ARGS=pipeline\scripts\run_vggt_runtime.py
ROOMSPLAT_LEARNED_RUNTIME_PYTHON_PATH=C:\path\to\vggt-env\python.exe
ROOMSPLAT_LEARNED_MODEL_ROOT=C:\project\RoomSplat\data\models
ROOMSPLAT_LEARNED_CHECKPOINT_PATH=vggt\model.pt
ROOMSPLAT_LEARNED_CHECKPOINT_SHA256=<sha256>
ROOMSPLAT_LEARNED_CACHE_DIR=C:\project\RoomSplat\data\cache\learned-runtime
ROOMSPLAT_LEARNED_MIN_FREE_VRAM_MB=10000
ROOMSPLAT_LEARNED_RUNTIME_TIMEOUT_SECONDS=1800
```

Compute the checkpoint hash:

```powershell
Get-FileHash C:\project\RoomSplat\data\models\vggt\model.pt -Algorithm SHA256
```

## Wrapper contract

`pipeline/scripts/run_vggt_runtime.py` implements the RoomSplat learned runtime command contract:

```text
python pipeline\scripts\run_vggt_runtime.py ^
  --frames-dir <selected-frames> ^
  --output-dir <output-dir> ^
  --checkpoint <checkpoint> ^
  --max-frames 12 ^
  --image-max-size 768 ^
  --precision fp16 ^
  --frame-index-map 0,1,2
```

Optional wrapper arguments:

- `--device auto|cuda|cpu`
- `--max-points`
- `--confidence-threshold`
- `--dry-run`

The wrapper writes:

- `.complete.json`
- `points.ply`
- `traj.txt` when camera predictions are available
- `intrinsics.txt` when camera predictions are available
- `sampling.json`

RoomSplat then imports the folder through `import_learned_geometry`, writes `metadata/geometry_bundle.json`, and labels the primary PLY as `predicted_point_cloud_ply`.

## Tiny smoke settings

Start with:

```text
adapter: vggt
max_frames: 8-12
frame_step: 1
image_max_size: 768
precision: fp16 or bfloat16
allow_cpu_offload: false
```

If preflight reports less than the configured free VRAM budget, close other GPU apps or lower `ROOMSPLAT_LEARNED_MIN_FREE_VRAM_MB` only for an intentional small experiment. The current local preflight observed an RTX 3080 Ti with 12,288 MB total VRAM and 8,878 MB free, which correctly blocks the default 10 GB smoke budget.

## Current local status

As of the first real local VGGT smoke follow-up:

- `pipeline/scripts/run_vggt_runtime.py --help` works.
- VGGT is cloned into ignored `data/tools/vggt` and installed editable into the existing Python 3.10 CUDA env.
- The local env has `torch==2.1.2+cu118`, `torchvision==0.16.2+cu118`, `vggt`, `safetensors`, `huggingface_hub`, `einops`, `opencv-python`, and `numpy==1.26.4`.
- `facebook/VGGT-1B` `model.pt` is stored under ignored `data/models/vggt/model.pt`.
- Checkpoint SHA-256: `D15BF50A8615C8225ED48B51EA5CAC673D82442EC0309036DF555A053253AFE0`.
- `.env` is configured locally with the VGGT runtime command, wrapper path, model root, checkpoint path/SHA, learned cache dir, 7 GB minimum free VRAM, and 30 minute timeout.
- A 4-frame smoke with `image_max_size=518`, `precision=fp16`, and `allow_cpu_offload=false` succeeded on project `9522ce63dbfc454fb638fae38375863c`.
- The smoke imported `reconstruction/learned-point-cloud.ply` as `predicted_point_cloud_ply` with 100,000 points and wrote `metadata/geometry_bundle.json`.
- Browser verification selected `learned-point-cloud.ply` and rendered a nonblank Three.js viewer frame.
- The wrapper and RoomSplat runtime handoff remain covered by dry-run/contract tests and fake-runtime import tests.

Next local experiments should increase frame count gradually toward 8-12 frames, then inspect whether object quality improves before raising image size.
