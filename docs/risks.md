# Risks

## High risk: Gaussian Splatting is not the same as metric mapping

Gaussian Splatting is excellent for view synthesis and visually reconstructing scenes, but it is not automatically a clean, metric, object-aware point cloud. The app must label output types honestly.

Mitigation:

- Keep artifact metadata explicit.
- Add docs explaining splat vs point cloud vs mesh.
- Add optional Open3D inspection path.

## High risk: Windows-native 3DGS dependencies

Some research tooling is easier on Linux or WSL. Windows native may be possible but fragile.

Mitigation:

- Make reconstruction path a spike milestone.
- Document exact dependency setup.
- Stop before switching to Docker/WSL unless project owner approves.

## Medium risk: `.glb` export uncertainty

GLB needs a mesh/scene representation. Direct splat-to-GLB may not be straightforward.

Mitigation:

- Support `.ply` first.
- Add `.glb` placeholder contract early but mark real export as dependent on representation.
- Implement real `.glb` when conversion path is proven.

## Medium risk: video quality affects reconstruction

Bad capture motion, blur, reflective surfaces, low light, and weak texture can break reconstruction.

Mitigation:

- Keep capture guidance short and visible.
- Validate input and show warnings.
- Keep sample datasets small and controlled.

## Medium risk: long-running jobs

Training/reconstruction may take a long time and fail late.

Mitigation:

- Implement job status/logging early.
- Save intermediate state.
- Preserve error output.

## Medium risk: exposing the local API

The v1 app has no authentication and is intended for localhost use.

Mitigation:

- Bind backend startup examples to `127.0.0.1`.
- Document that CORS is not authentication.
- Do not expose the backend to untrusted networks until an auth/security model is added.

## Medium risk: untrusted media resource usage

Uploaded media and extraction can consume memory, CPU, and disk.

Mitigation:

- Enforce a configurable upload size limit.
- Enforce an ffmpeg timeout.
- Keep frame extraction bounded with stride and max-frame options.

## Medium risk: learned reconstruction checkpoints and research runtimes

LingBot-Map/VGGT-style feed-forward reconstruction is promising, but research repos often depend on large model checkpoints, CUDA-specific packages, automatic downloads, and server/viewer assumptions that do not match RoomSplat's local-only Windows baseline.

Mitigation:

- Add a RoomSplat-native geometry bundle contract before integrating any learned model runtime.
- Require manual model/checkpoint paths by default.
- Use checksums or explicit allowlists before loading large model files.
- Keep learned adapters optional and isolated from the backend runtime.
- Report missing CUDA/GPU/model dependencies as blocked diagnostics.
- Keep all generated depth, NPZ, point, video, mask, and checkpoint outputs contained under the ignored project data directory.
- Do not expose no-auth viewers or APIs beyond `127.0.0.1`.

Current Milestone 11 controls:

- Checkpoints must resolve under `ROOMSPLAT_LEARNED_MODEL_ROOT`.
- `ROOMSPLAT_LEARNED_CHECKPOINT_SHA256` must match before smoke execution is considered ready.
- `learned_runtime_preflight` reports GPU, PyTorch/CUDA, checkpoint, selected frames, and VRAM budget diagnostics before runtime execution.
- `learned_runtime_smoke` imports successful output through the geometry bundle path and otherwise returns blocked diagnostics without fake geometry.
- A 12 GB RTX 3080 Ti is a plausible small-smoke target, but checkpoint size on disk is not a VRAM estimate; frame count, resolution, precision, activations, and runtime overhead still need caps.
