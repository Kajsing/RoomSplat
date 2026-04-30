# Architecture

## Overview

The system is a local hosted web app with a Python backend, React frontend, and local reconstruction pipeline.

```text
Browser UI
  ↓ HTTP
FastAPI backend
  ↓ services
Project storage + job store
  ↓ worker
Video/frame/reconstruction pipeline
  ↓ artifacts
Viewer/export endpoints
```

## Data flow
1. User creates project.
2. User imports video.
3. Backend copies video into project `input/`.
4. Frame extraction creates images in `frames/` and writes metadata.
5. Reconstruction job consumes frames and produces artifacts in `reconstruction/`.
6. Export service creates user-facing files in `exports/`.
7. Frontend displays artifacts through browser viewer or download links.
