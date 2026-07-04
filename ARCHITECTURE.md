# Architecture

## Overview

The system is a local hosted web app with a Python backend, React frontend, and local reconstruction pipeline.

```text
Browser UI
  -> HTTP
FastAPI backend
  -> services
Project storage + job store
  -> worker
Video/frame/reconstruction pipeline
  -> artifacts
Viewer/export endpoints
```

## Components

### Frontend

Responsibilities:

- Create/list projects.
- Upload/import video.
- Trigger frame extraction and reconstruction jobs.
- Show job status and logs.
- Display result artifacts.
- Provide export/download links.

Non-responsibilities:

- Running reconstruction algorithms.
- Direct filesystem writes.
- Heavy video processing.

### Backend

Responsibilities:

- Serve local API.
- Validate user actions.
- Manage project metadata.
- Manage job lifecycle.
- Invoke pipeline services/workers.
- Serve artifacts to the local UI.

Non-responsibilities:

- Implementing low-level 3DGS algorithms from scratch.
- Cloud sync.
- Public internet exposure.
- Authentication for v1 local-only use.

### Pipeline

Responsibilities:

- Inspect videos.
- Extract frames.
- Run or adapt reconstruction tools behind a small adapter contract.
- Export artifacts.
- Report dependency and processing errors clearly.

### Reconstruction adapter boundary

The reconstruction layer should call adapters by capability and artifact contract, not by hard-coded tool internals.

Current adapter contract:

```text
ReconstructionInput
  frames_dir
  frame_count
  width
  height

ReconstructionAdapter
  assess(input) -> AdapterAssessment

AdapterAssessment
  status
  dependency checks
  expected artifact contracts
  next setup steps
```

The interim path is:

```text
frames -> COLMAP/pycolmap poses -> Nerfstudio Splatfacto -> splat.ply
```

Future learned or generative splat methods should fit behind the same boundary by consuming frames and/or poses and emitting the same `splat_ply` artifact contract.

### Project storage

Each project gets its own folder. The backend is the only layer that should write to project folders directly.

### Artifact viewer boundary

The backend discovers result artifacts and labels them before the frontend displays them. The frontend must not infer that a file is a real reconstruction merely because it exists.

Current viewer behavior:

- `debug_frame_cloud_ply`: Three.js point cloud view of Frame Room Cloud debug artifacts sampled from extracted frames; not reconstruction. The viewer can show frame markers from `metadata/debug_frame_cloud.json`.
- `point_cloud_ply`: Three.js point cloud view with orbit, pan, zoom, point size, color mode, grid, and axes controls.
- `splat_ply`: attempts GaussianSplats3D rendering first; if the loader rejects the file, falls back to point-cloud preview with an explicit message.
- `mesh_glb`: Three.js GLB scene loading through `GLTFLoader`.
- `debug_report`: JSON/debug text, not a 3D artifact.

The first splat-first viewer test artifact is Frame Room Cloud: a deterministic ASCII PLY with XYZ + RGB points, capped at 50,000 points, arranged as vertical frame planes along a shallow arc. It accepts `max_points`, `frame_step`, `arc_degrees`, and `plane_width` job params. It exists to test viewer UX and spatial orientation before real reconstruction is integrated.

Viewer controls include large-view mode, reset/fit, front/side/top/default camera presets, screenshot capture, point size, color mode, grid/axes toggles, artifact stats, and debug warnings.

Expected future real splat artifact contract:

- `reconstruction/splat.ply` or another backend-labeled `splat_ply` artifact.
- Metadata should identify the reconstruction adapter, source frames/poses, generated time, and whether the artifact is a real reconstruction.
- The frontend attempts GaussianSplats3D rendering first for `splat_ply`; if parsing fails, it displays a point-cloud fallback with diagnostics rather than changing the backend label.

### Export boundary

The export service creates user-facing files in `exports/` from backend-listed artifacts and writes metadata in `metadata/exports/`.

Current export behavior:

- Real `.ply` and `.glb` exports are copies of existing same-format artifacts.
- Placeholder `.ply` and `.glb` exports can only be generated from the reconstruction spike debug report with an explicit placeholder flag.
- Export metadata records source artifact, output path, format, artifact label, generated time, download URL, and `real` or `placeholder` status.
- Placeholder exports must never be presented as real reconstruction output.

## Data flow

1. User creates project.
2. User imports video.
3. Backend copies video into project `input/`.
4. Backend creates a local job under `metadata/jobs/`.
5. Local worker runs frame extraction, creates images in `frames/`, and writes metadata.
6. Optional debug-frame-cloud job consumes `metadata/frame_extraction.json` and `frames/`, then writes `reconstruction/debug-frame-room.ply` and `metadata/debug_frame_cloud.json`.
7. Reconstruction-spike job consumes frames and writes dependency/output-contract guidance.
8. Future reconstruction job consumes frames and produces artifacts in `reconstruction/`.
9. Artifact service labels reconstruction/export/debug files.
10. Export service creates user-facing files in `exports/`.
11. Frontend displays artifacts through browser viewer states or download links.

## Error handling

- External tool failures are captured as job failures.
- Missing dependencies produce actionable setup messages.
- Invalid input files are rejected with clear errors.
- Failed jobs keep logs.
- Oversized uploads are rejected before import.
- Long ffmpeg extraction runs time out with a frame extraction error.

## Configuration

Use environment variables and `.env.example` for:

- Data directory.
- Backend host/port.
- Frontend backend URL.
- Optional external tool paths.
- Max upload size.
- Frame extraction defaults.
- ffmpeg timeout.

## Plugin architecture, later

Kinect support should be added as an input plugin, not baked into the core.

Future plugin interface:

```text
InputProvider
  name
  capabilities
  start_capture()
  stop_capture()
  export_session_to_project()
```
