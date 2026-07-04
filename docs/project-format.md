# Project Format

Each scan project is stored under the configured local data directory. The backend owns writes to project folders.

```text
project-root/
  metadata/
    project.json
    video_import.json
    frame_extraction.json
    reconstruction_spike.json
  input/
    source videos
  frames/
    frame_000001.png
    frame_000002.png
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
- Project folders are created under the configured data directory and named by project ID.
- Project metadata records source video and frame extraction settings before reconstruction jobs exist.
- `reconstruction_spike.json` records adapter readiness and selected interim reconstruction path when the spike is run.
- Future job metadata should record job status and artifact types.
- All paths must stay inside the configured data directory.
