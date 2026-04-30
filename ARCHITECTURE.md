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

### Pipeline

Responsibilities:

- Inspect videos.
- Extract frames.
- Run or adapt reconstruction tools.
- Export artifacts.
- Report dependency and processing errors clearly.

### Project storage

Each project gets its own folder. The backend is the only layer that should write to project folders directly.

## Data flow

1. User creates project.
2. User imports video.
3. Backend copies video into project `input/`.
4. Frame extraction creates images in `frames/` and writes metadata.
5. Reconstruction job consumes frames and produces artifacts in `reconstruction/`.
6. Export service creates user-facing files in `exports/`.
7. Frontend displays artifacts through browser viewer or download links.

## Error handling

- External tool failures are captured as job failures.
- Missing dependencies produce actionable setup messages.
- Invalid input files are rejected with clear errors.
- Failed jobs keep logs.

## Configuration

Use environment variables and `.env.example` for:

- Data directory.
- Backend host/port.
- Frontend backend URL.
- Optional external tool paths.
- Max upload size.
- Frame extraction defaults.

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
