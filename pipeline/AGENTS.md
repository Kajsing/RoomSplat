# Pipeline Agent Instructions

This directory contains reconstruction pipeline adapters and scripts.

## Rules

- Wrap external reconstruction tools behind adapter interfaces.
- Do not bind the whole app directly to one experimental tool.
- Start with safe inspection/spike scripts before integrating heavy training into the web app.
- Keep outputs deterministic where possible.
- Every adapter must document required external dependencies and expected outputs.
- Prefer existing tools for Gaussian Splatting / NeRF instead of implementing algorithms from scratch.
- If COLMAP or pycolmap is required for camera pose estimation, document it as an internal dependency of the chosen reconstruction path.

## Output contract

Pipeline steps should write into project folders using this general layout:

```text
project-root/
  input/
  frames/
  reconstruction/
    metadata.json
    cameras.json
    splat.ply
    pointcloud.ply
    scene.glb
  exports/
    result.ply
    result.glb
```

## Validation

Run pipeline tests before considering pipeline changes complete:

```bash
python -m pytest pipeline/tests
```
