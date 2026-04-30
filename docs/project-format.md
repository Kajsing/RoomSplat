# Project Format

Each scan project is stored under the configured local data directory. The backend owns writes to project folders.

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

## Artifact labels

- `pointcloud.ply` is a conventional point cloud if produced by the selected pipeline.
- `splat.ply` is Gaussian splat data and must not be labeled as a conventional point cloud.
- `scene.glb` / `result.glb` are portable scene exports when a conversion path exists.

## Storage rules

- Keep generated videos, frames, models, splats, checkpoints, and exports out of Git.
- Project metadata should record source video, frame extraction settings, job status, and artifact types.
- All paths must stay inside the configured data directory.
