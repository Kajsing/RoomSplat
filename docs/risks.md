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
