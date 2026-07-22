# Local learned runtime plan update

## Context

The project already has:

- a browser 3D viewer that can inspect point clouds, GLB files, splat-labeled PLYs through fallback, predicted point clouds, and geometry bundle metadata;
- a real local Nerfstudio/Splatfacto smoke path that can create `reconstruction/splat.ply`;
- a learned geometry bundle contract;
- a learned geometry preflight/import path for completed local output folders.

The target Windows machine has an NVIDIA RTX 3080 Ti with 12 GB VRAM. This makes a small local learned-geometry runtime smoke path plausible, but not guaranteed for unrestricted frame count or full-resolution input.

## Decision

Milestone 11 should test a controlled local learned-runtime path before further broad viewer polishing.

The next path is:

```text
video -> frames -> learned runtime preflight -> small learned smoke job -> completed learned output folder -> geometry bundle import -> browser viewer
```

## Guardrails

- No automatic model/checkpoint downloads by default.
- User-supplied checkpoint paths only.
- Checksum or explicit allowlist metadata before loading large checkpoints.
- Generated outputs, caches, and checkpoints stay out of Git.
- Runtime must report blocked diagnostics instead of fake geometry.
- GPU preflight should document device, CUDA/PyTorch readiness, memory budget, frame/keyframe limits, resize policy, precision, and offload assumptions.
- Tablet support stays a stretch capture/viewer workflow; tablet on-device inference is deferred.

## Remaining risks

- A checkpoint around 5 GB on disk may need substantially more than 5 GB VRAM during inference.
- Windows CUDA/PyTorch/model package compatibility may be fragile.
- Some learned model outputs may need adapter-specific conversion before they match RoomSplat's geometry bundle contract.
- Viewer native splat loading is still a separate compatibility issue; predicted point-cloud inspection is enough for the first learned-runtime smoke path.

## Validation

This entry records a planning/documentation update only. Implementation validation belongs to Milestone 11.
