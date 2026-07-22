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

## Milestone 9 - Learned Geometry Adapter Readiness

Goal: Prepare RoomSplat for optional feed-forward / learned reconstruction adapters that produce depth, confidence, camera poses, intrinsics, trajectories, and pointmap-style geometry without making any specific research model a core dependency.

Inspiration sources:

- Local reference copy: `C:\project\lingbot-map`.
- LingBot-Map-style output contracts: per-frame RGB/depth/confidence/points plus scene-level cameras, intrinsics, trajectory, point cloud, sampling metadata, and completion markers.

Acceptance criteria:

- Define a RoomSplat-native geometry bundle contract under project `metadata/` that can describe:
  - source adapter and schema version,
  - frame count and frame index mapping,
  - camera poses, intrinsics, and trajectory,
  - optional depth/confidence/mask availability,
  - primary artifacts and sidecar files,
  - quality notes, warnings, completion status, and generated-data rules.
- Keep the contract independent of COLMAP, Nerfstudio, LingBot-Map, or any single model internals.
- Add or update adapter interfaces so future learned adapters can return a normalized artifact bundle instead of writing arbitrary files directly into project folders.
- Extend artifact/documentation language for `predicted_point_cloud` / `learned_geometry` outputs so they are not confused with Gaussian splats, COLMAP sparse point clouds, meshes, or metric scans.
- Add viewer planning for confidence filtering, frame selector, current-frame/all-frames display, clickable camera/frustum inspection, camera downsampling, and trajectory inspection.
- Document dependency and safety rules for experimental learned adapters:
  - no automatic model or dataset downloads by default,
  - user-supplied model/checkpoint paths only,
  - checksum or explicit allowlist before loading large model files,
  - isolated local environment,
  - localhost-only UI/server assumptions,
  - generated outputs capped and contained under the project data directory,
  - missing GPU/CUDA/model dependencies reported as blocked diagnostics, not fake artifacts.
- Add focused tests for geometry bundle validation, path containment, artifact labeling, incomplete bundle rejection, and viewer/API type handling.

Validation:

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
git diff --check
git status --short
```

Stop condition:

Stop before adding a direct LingBot-Map or similar model runtime dependency if it requires changing RoomSplat's Windows-native, local-only, no-cloud, or no-paid-dependency assumptions. Document the alternative and ask before changing direction.

## Future milestones, not v1

- Live stream/webcam ingestion.
- Android companion app.
- Kinect for Windows plugin.
- Better measurement tools.
- Dense mesh generation.
- Better GLB conversion.
- Experimental LingBot-Map/VGGT-style learned geometry adapter after Milestone 9 contracts and safety rules are in place.
- Packaged Windows installer.
