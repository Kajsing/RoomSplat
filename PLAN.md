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
