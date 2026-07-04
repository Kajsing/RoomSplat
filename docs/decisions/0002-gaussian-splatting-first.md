# Decision 0002: Gaussian Splatting / NeRF First

## Status

Accepted as project direction; interim adapter-first path selected by Milestone 4 spike.

## Context

The project owner selected Gaussian Splatting / NeRF-style reconstruction over a traditional-only photogrammetry or point-cloud project.

## Decision

Pursue Gaussian Splatting / NeRF first through an adapter boundary rather than binding the app directly to one experimental tool.

The selected interim path is:

```text
frames -> COLMAP/pycolmap camera poses -> Nerfstudio Splatfacto -> splat.ply
```

This is an interim path, not a permanent product lock-in. The backend, job system, metadata, and UI should depend on artifact contracts such as `camera_poses`, `point_cloud_ply`, and `splat_ply`, not on Nerfstudio-specific command details.

`gsplat` remains the lower-level adapter boundary for future faster custom, learned, or generative splat approaches. Open3D remains optional debug tooling for conventional point clouds and should not be treated as a Gaussian Splatting trainer.

Primary references checked during the spike:

- Nerfstudio Windows install notes: https://docs.nerf.studio/quickstart/installation.html
- Nerfstudio Splatfacto method notes: https://docs.nerf.studio/nerfology/methods/splat.html
- PyCOLMAP install docs: https://colmap.github.io/pycolmap/index.html
- COLMAP overview: https://colmap.github.io/
- gsplat Windows install notes: https://github.com/nerfstudio-project/gsplat/blob/main/docs/INSTALL_WIN.md
- Open3D getting started: https://www.open3d.org/docs/release/getting_started.html

## Consequences

- The pipeline must honestly distinguish Gaussian splat data from conventional point clouds and meshes.
- Milestone 4 does not install heavy dependencies by default; it validates frames, reports dependency readiness, and records stop-condition guidance.
- Windows-native Nerfstudio/gsplat remains fragile because of CUDA, PyTorch, Visual Studio Build Tools, and compiler environment requirements.
- PyCOLMAP has pre-built Windows wheels and is the preferred first pose-estimation dependency to test.
- The app must not pretend placeholder outputs are real reconstructions.
- A future fast/generative splat adapter can replace the interim training path if it emits the same artifact contract.
