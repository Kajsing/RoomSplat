# Local learned runtime smoke path

## Goal

Implement Milestone 11: a controlled local learned-geometry runtime smoke path for Windows/RTX 3080 Ti-class use, without bundling LingBot-Map/VGGT, downloading checkpoints, changing the local-only model, or creating fake geometry.

## Implementation

- Added `pipeline.adapters.learned_runtime`.
- Added `backend.app.services.learned_runtime.LearnedRuntimeService`.
- Added job types:
  - `learned_runtime_preflight`
  - `learned_runtime_smoke`
- Added config fields for:
  - local adapter command and fixed args,
  - runtime Python diagnostics path,
  - model root,
  - checkpoint path,
  - checkpoint SHA-256,
  - learned runtime cache dir,
  - minimum free VRAM,
  - runtime timeout.
- Added frontend job controls for runtime adapter, max frames, frame step, image max size, precision, CPU/offload, preflight, and smoke.

## Safety

- No automatic checkpoint download.
- Checkpoints must resolve under `ROOMSPLAT_LEARNED_MODEL_ROOT`.
- Smoke readiness requires checkpoint SHA-256 to match `ROOMSPLAT_LEARNED_CHECKPOINT_SHA256`.
- Runtime command is executed with an argument list, not through a shell command string.
- Stored command diagnostics redact the checkpoint path.
- Selected frames and runtime output folders are created under the selected project folder.
- Successful output is imported through the existing learned geometry import path and validated as `metadata/geometry_bundle.json`.
- Blocked statuses do not create placeholder geometry.

## Test shape

Tests use a fake local adapter script that accepts the runtime command contract and writes a tiny completed learned-output folder. This validates the handoff without requiring a real checkpoint, CUDA, or external research repo in CI.

## Current limitation

This milestone adds the runtime boundary and smoke path. A real LingBot/VGGT-style wrapper still needs to be configured locally and tested on the RTX 3080 Ti with a small frame/resize/precision budget.
