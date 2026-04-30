# Local 3D Room Mapper — Codex Handoff Spec

## Bootstrap prompt for Codex

You are working in a new Git repository for a local 3D reconstruction project.

Your first job is **not** to freestyle an implementation. Your first job is to create the repository structure, project documentation, validation commands, and minimal runnable skeleton described below. After the skeleton is created, implement the project milestone-by-milestone from `PLAN.md`.

Follow this order:

1. Create the repository structure exactly as specified unless there is a strong technical reason not to.
2. Create `AGENTS.md`, `PLAN.md`, `IMPLEMENT.md`, `DOCUMENTATION.md`, `SPEC.yaml`, `ARCHITECTURE.md`, and `README.md` first.
3. Create a minimal local hosted web app skeleton that can start on Windows.
4. Run validation commands after each milestone.
5. Log progress in `.logs/` and update `DOCUMENTATION.md` continuously.
6. Stop and ask for clarification only when a decision blocks safe implementation.

Do not silently expand scope. Do not replace the Gaussian Splatting/NeRF direction with a traditional-only photogrammetry project unless the spike proves the chosen direction is impossible for local Windows execution.

---

# 1. Project intent

## Working title

`local-3d-room-mapper`

## One-sentence goal

Build a local hosted web app that can take a video recording, and later a live stream, and generate a simple 3D map of rooms and objects using a Gaussian Splatting / NeRF-style reconstruction pipeline, with export support for `.ply` and `.glb`.

## Primary user

The first user is Christian, a technical power user on Windows who is comfortable with Python, Git, VS Code, WSL, Docker, and local AI/computer-vision tools. The project should still be structured as a public Git project that other technical users can clone, inspect, run, and extend.

## Product shape

This is **not** primarily an Android app in v1. Android phones/tablets are capture devices. The main app runs locally on a Windows PC and exposes a local browser UI.

## Core principle

First build the engine that can eat a video and spit out a 3D result. Then add stream capture, Android companion workflows, and Kinect plugins later.

---

# 2. Fixed decisions from project owner

These are locked unless a spike proves them technically impossible.

```yaml
program_type: local_hosted_webapp
runtime: windows_native_first
reconstruction_direction: gaussian_splatting_or_nerf_first
input_v1: imported_video_file_first
input_v1_1: stream_from_phone_or_webcam_later
viewer: both_browser_viewer_and_desktop_debug_viewer
exports: [ply, glb]
storage: local_project_folders
cloud_dependency: none_by_default
privacy: local_only_no_upload_without_explicit_user_action
android_role_v1: capture_device_only
kinect_role_v1: not_required_plugin_later
```

---

# 3. Important assumptions

Mark these clearly in generated docs.

1. **ASSUMPTION:** The user has an NVIDIA GPU capable of running local PyTorch/CUDA workloads, or is willing to accept CPU/low-performance fallback for non-training parts.
2. **ASSUMPTION:** Windows native execution is preferred over Docker for v1.
3. **ASSUMPTION:** Gaussian Splatting / NeRF is the preferred reconstruction direction, but the pipeline may need COLMAP, pycolmap, or another camera-pose estimation step internally.
4. **ASSUMPTION:** `.ply` may represent either a conventional point cloud or Gaussian splat data depending on pipeline stage. The app must label these clearly.
5. **ASSUMPTION:** `.glb` export may require conversion from mesh/point/splat representation and may be partial in early milestones.
6. **ASSUMPTION:** Accuracy target is “roughly measurable / visually useful”, not construction-grade.
7. **ASSUMPTION:** The first milestone should prioritize a working end-to-end path over beautiful reconstruction quality.

---

# 4. Non-goals for v1

Do not implement these in v1 unless explicitly requested later.

- Native Android application.
- Cloud processing.
- User accounts.
- Multi-user collaboration.
- Production-grade security hardening.
- Construction-grade measurement precision.
- Real-time SLAM.
- Perfect object segmentation.
- Full Kinect support.
- Mobile GPU processing.
- Commercial polish.

---

# 5. Codex-oriented repository strategy

## Why this structure

Codex performs best on long-horizon tasks when the repo contains small, durable instruction files instead of one giant prompt. Use:

- `AGENTS.md` for persistent project rules and behavioral constraints.
- `PLAN.md` for milestone order, acceptance criteria, and validation commands.
- `IMPLEMENT.md` for the execution runbook.
- `DOCUMENTATION.md` as the living status, decisions, and demo log.
- `.logs/` for detailed work logs per run/milestone.
- Optional nested `AGENTS.md` files for backend/frontend/pipeline-specific rules.
- Optional repo-scoped skills under `.agents/skills/` later if repeated workflows emerge.

Avoid putting the entire project spec into `AGENTS.md`. Keep `AGENTS.md` short enough that it is reliably loaded, and make it reference the other files as sources of truth.

## Instruction precedence to respect

Codex can load global instructions from the user’s Codex home directory and project instructions from the repository. Project-level instructions should be placed at the repo root. More specific nested instruction files can override root guidance for subdirectories.

For this project, start Codex from the repository root unless working on a submodule with a deliberate nested `AGENTS.md`.

---

# 6. Desired repository structure

```text
local-3d-room-mapper/
  AGENTS.md
  PLAN.md
  IMPLEMENT.md
  DOCUMENTATION.md
  SPEC.yaml
  ARCHITECTURE.md
  README.md
  pyproject.toml
  package.json
  .gitignore
  .env.example

  backend/
    AGENTS.md
    app/
      __init__.py
      main.py
      config.py
      api/
        __init__.py
        routes_health.py
        routes_projects.py
        routes_uploads.py
        routes_jobs.py
        routes_exports.py
      services/
        __init__.py
        project_store.py
        job_store.py
        video_import.py
        frame_extraction.py
        reconstruction_jobs.py
        export_service.py
      models/
        __init__.py
        schemas.py
      workers/
        __init__.py
        local_worker.py
    tests/
      test_health.py
      test_project_store.py
      test_video_import.py

  frontend/
    AGENTS.md
    index.html
    package.json
    vite.config.ts
    tsconfig.json
    src/
      main.tsx
      App.tsx
      api.ts
      components/
        ProjectList.tsx
        UploadPanel.tsx
        JobStatusPanel.tsx
        ViewerPanel.tsx
      viewer/
        pointCloudViewer.ts
        glbViewer.ts
    tests/
      smoke.test.ts

  pipeline/
    AGENTS.md
    README.md
    scripts/
      extract_frames.py
      inspect_video.py
      run_reconstruction_spike.py
      export_ply.py
      export_glb.py
    adapters/
      __init__.py
      nerfstudio_adapter.py
      gsplat_adapter.py
      colmap_adapter.py
      open3d_adapter.py
    tests/
      test_frame_extraction.py
      test_export_contracts.py

  docs/
    decisions/
      0001-local-webapp-windows-native.md
      0002-gaussian-splatting-first.md
      0003-video-first-stream-later.md
    risks.md
    capture-guide.md
    validation.md
    project-format.md
    plugin-kinect-notes.md

  examples/
    README.md
    sample-project-placeholder.md

  data/
    .gitkeep

  .logs/
    README.md
```

`data/` must be ignored by Git except `.gitkeep`. Generated videos, frames, models, splats, exports, and local project folders must not be committed.

---

# 7. Root `AGENTS.md` content to create

Create this file at repository root.

```markdown
# Local 3D Room Mapper — Agent Instructions

## Project role

You are implementing a local Windows-first 3D reconstruction web app. The app imports video, extracts frames, runs a local Gaussian Splatting / NeRF-style reconstruction pipeline, and exports `.ply` and `.glb` outputs.

## Sources of truth

Read these before changing code:

1. `SPEC.yaml` — product and technical requirements.
2. `PLAN.md` — milestone sequence, acceptance criteria, validation commands.
3. `IMPLEMENT.md` — execution rules.
4. `ARCHITECTURE.md` — module boundaries and data flow.
5. `DOCUMENTATION.md` — current status, decisions, known issues.

If these files conflict, follow this precedence:

1. User prompt.
2. `AGENTS.md`.
3. `SPEC.yaml`.
4. `PLAN.md`.
5. `IMPLEMENT.md`.
6. Other docs.

## Working rules

- Keep diffs scoped to the current milestone.
- Do not silently expand product scope.
- Prefer a minimal working vertical slice over broad unfinished scaffolding.
- Run validation commands after each milestone.
- Fix failing validations before moving to the next milestone.
- Update `DOCUMENTATION.md` after meaningful changes.
- Log work under `.logs/` when a task involves investigation, tradeoffs, or multiple attempts.
- Keep generated data out of Git.
- Do not commit videos, extracted frames, trained splats, model checkpoints, or large exports.
- Do not add cloud dependencies unless explicitly requested.
- Do not require Docker for v1 unless Windows-native execution proves impractical.

## Technical defaults

- Backend: Python + FastAPI.
- Frontend: Vite + React + TypeScript.
- Viewer: browser-based Three.js viewer plus optional Open3D debug tools.
- Runtime: Windows native first.
- Long-running work: local job queue / background worker.
- Storage: local project folders under a configurable data directory.
- Exports: `.ply` and `.glb`.
- Reconstruction direction: Gaussian Splatting / NeRF first, using existing tools where practical.

## Stop conditions

Stop and ask for clarification if:

- A selected core decision is impossible without changing product direction.
- A new paid/commercial dependency is required.
- A dependency requires cloud upload.
- A change would require committing large binary data.
- Validation cannot be made to pass after reasonable focused repair.

## Validation expectations

At minimum, keep these working:

- Backend health endpoint test.
- Frontend build.
- Frame extraction test using synthetic or tiny sample media.
- Export contract tests for `.ply` and `.glb` placeholder outputs.
- End-to-end smoke path: create project → upload/import video placeholder → extract frames → create job → produce/export placeholder or real artifact depending on milestone.
```

---

# 8. Backend `backend/AGENTS.md` content to create

```markdown
# Backend Agent Instructions

This directory contains the Python backend and local worker logic.

## Rules

- Use FastAPI for HTTP endpoints.
- Keep API schemas in `backend/app/models/schemas.py`.
- Keep business logic in `backend/app/services/`.
- Keep long-running job execution in `backend/app/workers/`.
- Endpoints should be thin wrappers over services.
- Validate paths carefully. Do not allow arbitrary filesystem access outside configured project/data directories.
- All file writes must go through the project storage service.
- Add or update tests when changing service behavior.

## Validation

Run backend tests before considering backend changes complete:

```bash
python -m pytest backend/tests pipeline/tests
```
```

---

# 9. Frontend `frontend/AGENTS.md` content to create

```markdown
# Frontend Agent Instructions

This directory contains the local browser UI.

## Rules

- Use React + TypeScript + Vite.
- Keep API access in `src/api.ts`.
- Keep rendering/viewer logic in `src/viewer/`.
- Keep components small and milestone-focused.
- The UI must support a local workflow: project list, video import, job status, result viewer, export links.
- Prefer robust simple UI over visual polish.
- Avoid adding large UI libraries unless needed.

## Validation

Run frontend checks before considering frontend changes complete:

```bash
npm --prefix frontend install
npm --prefix frontend run build
```
```

---

# 10. Pipeline `pipeline/AGENTS.md` content to create

```markdown
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
```

---

# 11. `PLAN.md` content to create

```markdown
# Implementation Plan

## Milestone 0 — Repository scaffold and docs

Goal: Create the repo structure, project docs, ignored data folders, and minimal build/test setup.

Acceptance criteria:

- `AGENTS.md`, `PLAN.md`, `IMPLEMENT.md`, `DOCUMENTATION.md`, `SPEC.yaml`, `ARCHITECTURE.md`, and `README.md` exist.
- Backend, frontend, pipeline, docs, examples, data, and `.logs` directories exist.
- `.gitignore` excludes generated data, Python caches, node modules, build outputs, videos, frames, models, splats, and exports.
- `DOCUMENTATION.md` records the initial status.

Validation:

```bash
python --version
node --version
```

## Milestone 1 — Minimal local hosted web app

Goal: Start a local FastAPI backend and Vite frontend.

Acceptance criteria:

- Backend exposes `GET /health` returning JSON status.
- Frontend loads in browser and displays backend health.
- README includes Windows startup commands.
- Backend test covers `/health`.

Validation:

```bash
python -m pytest backend/tests
npm --prefix frontend run build
```

## Milestone 2 — Local project storage

Goal: Create and list local scan projects.

Acceptance criteria:

- Backend can create a project with ID, name, created timestamp, and folder structure.
- Backend can list existing projects.
- Project metadata is stored as JSON.
- All project files remain under the configured data directory.
- Frontend shows project list and create-project flow.

Validation:

```bash
python -m pytest backend/tests
npm --prefix frontend run build
```

## Milestone 3 — Video import and frame extraction

Goal: Import a video file and extract frames into the project folder.

Acceptance criteria:

- Backend accepts a local upload or configured local file import.
- Imported video is copied into `input/`.
- Frame extraction writes frames into `frames/`.
- Frame extraction metadata records fps, frame count, extraction stride, resolution, and source video.
- Synthetic/tiny media test covers frame extraction.
- Frontend supports upload/import and shows extraction status.

Validation:

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

## Milestone 4 — Reconstruction spike: Gaussian Splatting / NeRF path

Goal: Determine and document the first working local Windows-native reconstruction path.

Candidate tools to evaluate:

- Nerfstudio Splatfacto / gsplat path.
- Existing Gaussian Splatting tooling with command-line support.
- COLMAP or pycolmap for camera poses if required.
- Open3D for point cloud inspection/conversion.

Acceptance criteria:

- `docs/decisions/0002-gaussian-splatting-first.md` is updated with the selected path.
- `pipeline/README.md` documents required dependencies and commands.
- `pipeline/scripts/run_reconstruction_spike.py` exists and either:
  - runs a real reconstruction on a small sample, or
  - prints a clear actionable message explaining missing external dependencies.
- The spike produces or defines the contract for `.ply` output.
- The app does not pretend that placeholder output is real reconstruction.

Validation:

```bash
python pipeline/scripts/run_reconstruction_spike.py --help
python -m pytest pipeline/tests
```

Stop condition:

If no Windows-native local path is practical, stop and document options before changing runtime direction.

## Milestone 5 — Job system for long-running reconstruction

Goal: Add local background jobs for extraction and reconstruction.

Acceptance criteria:

- Backend can create a job for frame extraction or reconstruction.
- Job status includes queued/running/succeeded/failed.
- Job logs are written to project folder or `.logs/`.
- Frontend polls and displays job status.
- Failed jobs preserve error messages.

Validation:

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

## Milestone 6 — Viewer integration

Goal: Display exported `.ply` and/or `.glb` results.

Acceptance criteria:

- Browser viewer can load at least one result artifact.
- Viewer supports rotate, pan, zoom.
- Viewer clearly labels artifact type: point cloud, splat PLY, mesh, or GLB.
- Optional desktop debug viewer script exists using Open3D if installed.

Validation:

```bash
npm --prefix frontend run build
python -m pytest backend/tests pipeline/tests
```

## Milestone 7 — Export service

Goal: Provide export links for `.ply` and `.glb`.

Acceptance criteria:

- Backend exposes export endpoints.
- Project artifacts can be downloaded from the UI.
- Export metadata records source artifact, generated time, and format.
- `.ply` and `.glb` outputs are clearly distinguished from raw intermediate files.

Validation:

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

## Milestone 8 — v1 hardening and docs

Goal: Make the app understandable, reproducible, and safe for public Git release.

Acceptance criteria:

- README has setup, run, test, and workflow instructions.
- Docs explain video capture tips.
- Docs explain limitations of Gaussian splats vs point clouds vs meshes.
- `.env.example` documents config.
- No generated data is tracked.
- A new user can run the minimal app on Windows.

Validation:

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
git status --short
```

## Future milestones, not v1

- Live stream/webcam ingestion.
- Android companion app.
- Kinect for Windows plugin.
- Better measurement tools.
- Dense mesh generation.
- Better GLB conversion.
- Packaged Windows installer.
```

---

# 12. `IMPLEMENT.md` content to create

```markdown
# Implementation Runbook

## Before coding

1. Read `AGENTS.md`.
2. Read `SPEC.yaml`.
3. Read `PLAN.md`.
4. Read `ARCHITECTURE.md`.
5. Read `DOCUMENTATION.md`.
6. Identify the current milestone.
7. Write a short entry in `.logs/` if the task is non-trivial.

## During coding

- Work on one milestone at a time.
- Keep diffs scoped.
- Prefer small, testable functions.
- Keep external tool integration behind adapters.
- Use placeholders only when clearly labeled as placeholders.
- Never present fake reconstruction output as real.
- Update docs when behavior changes.

## After each milestone

1. Run the milestone validation commands from `PLAN.md`.
2. Fix failures before moving on.
3. Update `DOCUMENTATION.md` with:
   - milestone status,
   - commands run,
   - test results,
   - decisions made,
   - known issues,
   - next step.
4. Add a `.logs/YYYY-MM-DD-milestone-N.md` entry if useful.

## Error handling philosophy

- Fail loudly with actionable messages.
- Preserve job logs.
- Do not swallow external tool errors.
- Surface missing dependency errors clearly in the UI and CLI.
- Avoid destructive cleanup unless explicitly requested.

## Dependency policy

- Prefer widely used open-source dependencies.
- Ask before adding paid/commercial tools as required dependencies.
- Optional integrations may be documented but must not block base app startup.
- Do not require cloud services.

## Security and filesystem policy

- Treat imported files as untrusted.
- Do not allow arbitrary file writes outside the configured data directory.
- Sanitize project names for filesystem use.
- Do not expose the local server publicly by default.
- Bind to localhost by default.

## Stop and ask when

- A milestone requires a major architecture change.
- External dependencies conflict with Windows-native execution.
- Reconstruction requires a paid/commercial CLI.
- GPU requirements exceed reasonable local assumptions.
- A user-facing decision affects project direction.
```

---

# 13. `DOCUMENTATION.md` content to create

```markdown
# Project Documentation and Status

## Current status

Status: Not implemented yet.
Current milestone: Milestone 0 — Repository scaffold and docs.

## Latest completed milestone

None.

## How to run

To be filled as implementation progresses.

## How to test

To be filled as implementation progresses.

## Decisions made

| Date | Decision | Reason |
|---|---|---|
| TBD | Local hosted web app | Keeps Android as capture device and avoids mobile performance constraints. |
| TBD | Windows-native first | Matches primary user environment. |
| TBD | Gaussian Splatting / NeRF first | Project owner selected splat/NeRF direction over traditional-only point cloud reconstruction. |
| TBD | Video import before stream | Reduces MVP complexity and creates reproducible test inputs. |
| TBD | Browser + desktop debug viewer | Browser is user-facing; desktop viewer helps pipeline debugging. |
| TBD | `.ply` + `.glb` exports | Open formats useful for point clouds/splats and broader 3D tooling. |

## Known issues

- No reconstruction pipeline selected yet.
- `.ply` may mean point cloud or splat data depending on pipeline stage; UI must label this.
- `.glb` export path is uncertain until representation is known.
- Windows-native GPU dependencies may be difficult.

## Commands run

None yet.

## Next step

Create repository scaffold and minimal runnable local web app.
```

---

# 14. `SPEC.yaml` content to create

```yaml
project:
  name: local-3d-room-mapper
  description: Local hosted web app for video-based 3D room/object reconstruction.
  owner_profile: technical_power_user_windows

product:
  goal: Build a local web app that imports video and generates a simple 3D map using Gaussian Splatting or NeRF-style reconstruction.
  target_users:
    - technical_owner
    - open_source_experimenters
  primary_workflow:
    - create_project
    - import_video
    - extract_frames
    - run_reconstruction
    - inspect_result
    - export_result
  non_goals_v1:
    - native_android_app
    - cloud_processing
    - multi_user
    - realtime_slam
    - construction_grade_measurement
    - kinect_required
    - production_auth

technical_decisions:
  app_type: local_hosted_webapp
  runtime: windows_native_first
  backend: python_fastapi
  frontend: react_typescript_vite
  reconstruction: gaussian_splatting_or_nerf_first
  viewer:
    browser: threejs
    desktop_debug: open3d_optional
  input_v1:
    - video_file
  input_future:
    - webcam_stream
    - phone_shared_webcam
    - android_companion_app
    - kinect_plugin
  exports:
    - ply
    - glb
  storage: local_project_folders
  privacy: local_only

quality_targets:
  reconstruction_quality: visually_useful_roughly_measurable
  performance_v1: best_effort_local
  startup: backend_and_frontend_start_on_windows
  reliability: fail_with_actionable_errors

project_storage_contract:
  root: configurable_data_directory
  structure:
    input: source_videos
    frames: extracted_frames
    reconstruction: intermediate_and_generated_3d_data
    exports: user_downloadable_outputs
    metadata: project_and_job_metadata

artifact_types:
  point_cloud_ply:
    description: Conventional colored point cloud if produced by pipeline.
  splat_ply:
    description: Gaussian splat data stored in PLY-like format; not equivalent to conventional point cloud.
  glb:
    description: Portable 3D scene/mesh container; availability depends on conversion path.

validation:
  backend:
    - python -m pytest backend/tests
  pipeline:
    - python -m pytest pipeline/tests
  frontend:
    - npm --prefix frontend run build
  full_smoke:
    - create project
    - import tiny video
    - extract frames
    - create reconstruction job
    - produce labeled placeholder or real artifact
    - load viewer
```

---

# 15. `ARCHITECTURE.md` content to create

```markdown
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
```

---

# 16. README content goals

The README should eventually contain:

1. What the project does.
2. What it does not do yet.
3. Windows setup.
4. Backend start command.
5. Frontend start command.
6. How to import a video.
7. How to run tests.
8. Where generated data is stored.
9. GPU/reconstruction dependency notes.
10. Status of Gaussian Splatting / NeRF integration.

---

# 17. Suggested initial dependency direction

Do not blindly install all of these in Milestone 0. Use them as likely candidates.

## Backend

- Python 3.11 or 3.12.
- FastAPI.
- Uvicorn.
- Pydantic.
- pytest.
- python-dotenv.

## Video/frame processing

- OpenCV Python.
- ffmpeg or imageio-ffmpeg.

## Reconstruction spike candidates

- Nerfstudio / Splatfacto.
- gsplat.
- COLMAP or pycolmap if required for camera poses.
- Open3D for point cloud handling/debug viewer.

## Frontend

- React.
- TypeScript.
- Vite.
- Three.js.

---

# 18. Risks

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

- Create `docs/capture-guide.md`.
- Validate input and show warnings.
- Keep sample datasets small and controlled.

## Medium risk: long-running jobs

Training/reconstruction may take a long time and fail late.

Mitigation:

- Implement job status/logging early.
- Save intermediate state.
- Preserve error output.

---

# 19. Open questions

Codex should not block Milestone 0–3 on these, but should record them.

1. Exact GPU and CUDA environment.
2. Preferred Python version on target Windows machine.
3. Whether Postshot or other commercial tools may be optional adapters.
4. Whether WSL/Docker fallback is allowed if Windows-native 3DGS fails.
5. Whether `.glb` must be true geometry or whether a viewer-compatible scene wrapper is acceptable.
6. How large videos should be supported in v1.
7. Whether phone stream should be browser-based, DroidCam-style webcam, RTSP, or Android companion app.
8. Whether Kinect for Windows is v2 or older v1 hardware.

---

# 20. Initial `.gitignore` requirements

Include at least:

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/
.pytest_cache/

# Node
node_modules/
frontend/dist/
*.tsbuildinfo

# Environment
.env
.env.local

# Local data and generated artifacts
data/**
!data/.gitkeep
*.mp4
*.mov
*.avi
*.mkv
*.webm
*.ply
*.glb
*.obj
*.fbx
*.ckpt
*.pt
*.pth
*.npz
*.npy
frames/
exports/
reconstruction/

# Logs
.logs/*.tmp
*.log

# OS/editor
.DS_Store
Thumbs.db
.vscode/
.idea/
```

---

# 21. First concrete Codex task

After creating the repository structure and docs, implement Milestone 1 only.

Expected Milestone 1 result:

- `backend/app/main.py` starts FastAPI.
- `GET /health` returns:

```json
{
  "status": "ok",
  "app": "local-3d-room-mapper",
  "version": "0.1.0"
}
```

- `frontend/src/App.tsx` fetches `/health` or configured backend URL and displays the status.
- Backend test passes.
- Frontend builds.
- README contains commands.

Do not implement reconstruction before Milestone 4. Do not fake reconstruction in the UI except as clearly labeled placeholder state for testing job flow.

