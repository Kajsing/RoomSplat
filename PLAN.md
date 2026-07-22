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

## Milestone 10 - Learned Geometry Import v1

Goal: Add a RoomSplat-native optional import/preflight path for completed local learned-geometry output folders, without adding LingBot-Map, VGGT, checkpoints, model downloads, cloud dependencies, or a required learned runtime.

Inspiration sources:

- Local reference copy: `C:\project\lingbot-map`.
- LingBot/BSS-style completed output folders with `.complete.json`, global `points.ply`, `traj.txt`, `intrinsics.txt`, `sampling.json`, and optional `depth/`, `confidence/`, `mask/`, and `points/` sidecar folders.

Acceptance criteria:

- Add pipeline preflight helpers that inspect a completed local learned-output folder and report expected geometry bundle artifacts and sidecars.
- Add backend job/API flow:
  - `learned_geometry_preflight` validates project frames plus source folder completeness without copying outputs.
  - `import_learned_geometry` copies the primary PLY to `reconstruction/learned-point-cloud.ply`, copies known sidecars under `metadata/learned/<adapter-slug>/`, writes `metadata/geometry_bundle.json`, and validates it.
- Keep all written output paths contained under the selected project folder.
- Reject missing extracted frames, missing `.complete.json`, missing primary PLY, escaped source-relative paths, missing declared sidecars, and out-of-range frame maps.
- Label imported PLY as `predicted_point_cloud_ply`, never `point_cloud_ply` or `splat_ply`.
- Keep imported learned geometry marked `is_reconstruction: false` and `not_reconstruction: true`.
- Update frontend job controls for learned geometry preflight/import.
- Display geometry bundle metadata separately from 3D artifacts in the viewer.
- Add focused backend, pipeline, and frontend helper tests.
- Update README, documentation, security notes, validation docs, and logs.

Validation:

```bash
python -m pytest backend/tests pipeline/tests
node --experimental-strip-types --test frontend/tests/*.test.ts
npm --prefix frontend run build
git diff --check
git status --short
```

Stop condition:

Stop before adding a direct learned-model runtime, checkpoint loader, automatic model download, public server binding, or non-local dependency. Document the alternative and ask before changing direction.

## Milestone 11 - Local Learned Runtime Smoke Path

Goal: Turn the learned-geometry contract/import path into a controlled local Windows GPU smoke path for the RTX 3080 Ti-class machine, while preserving local-only behavior, generated-data safety, and explicit model/checkpoint control.

Direction:

- Treat LingBot-Map/VGGT-style feed-forward geometry as the next primary reconstruction path to test locally.
- Keep Nerfstudio/Splatfacto as the existing real splat path, but do not block learned runtime work on native browser splat rendering compatibility.
- Use the browser viewer plus geometry bundle contract as the validation surface for first recognizable local learned output.
- Tablet support is a stretch capture/viewer workflow, not a v1 on-device inference requirement.

Acceptance criteria:

- Add a learned-runtime preflight that reports:
  - GPU availability and device name.
  - CUDA/PyTorch readiness when available.
  - total/free VRAM where observable.
  - configured checkpoint/model paths and missing dependency diagnostics.
  - estimated runtime budget from max frames, image resize, precision, and optional CPU/offload settings.
- Add explicit configuration for optional learned runtime dependencies:
  - no automatic model or checkpoint download by default,
  - user-supplied checkpoint paths only,
  - checksum or allowlist metadata before loading large model files,
  - generated outputs and caches kept under ignored local data/tool/cache folders,
  - clear docs for disk/VRAM expectations on a 12 GB GPU.
- Add an isolated adapter boundary for a local learned runtime invocation:
  - consumes existing extracted frames,
  - applies deterministic frame/keyframe selection,
  - supports resize/max-frame/runtime params,
  - writes a completed local learned-output folder or blocked diagnostics,
  - imports successful output through the existing `import_learned_geometry` / geometry bundle path.
- Add a first smoke command/job path that can run with a very small frame budget and either:
  - produce a valid `predicted_point_cloud_ply` + `learned_geometry_bundle`, or
  - fail as `blocked_missing_dependencies` / `blocked_missing_checkpoint` / `blocked_insufficient_vram` without fake artifacts.
- Update the frontend job controls to expose the preflight/smoke path without encouraging public server exposure or accidental checkpoint download.
- Viewer validation should prioritize:
  - recognizable geometry if runtime succeeds,
  - correct artifact labeling,
  - camera/path/depth/confidence metadata inspection where available,
  - no misleading promotion of predicted geometry as verified metric reconstruction.
- Add focused tests for preflight parsing, checkpoint path containment, no-auto-download behavior, frame budget validation, blocked diagnostics, geometry bundle import handoff, and frontend helper/job type handling.
- Update README, DOCUMENTATION.md, architecture notes, validation docs, security notes, and a `.logs/` entry with assumptions, known risks, and validation results.

Validation:

```bash
python -m pytest backend/tests pipeline/tests
node --experimental-strip-types --test frontend/tests/*.test.ts
npm --prefix frontend run build
git diff --check
git status --short
```

Manual/browser validation when dependencies are present:

```text
create/import project -> extract frames -> run learned runtime preflight -> run small learned smoke job -> import bundle -> inspect predicted PLY/bundle in viewer
```

Stop condition:

Stop before requiring cloud processing, a paid dependency, public server binding, committing checkpoints/generated outputs, or changing the local-only security model. If the selected learned runtime cannot run within a practical 12 GB VRAM budget after frame/resize/precision limits, document the failed preflight and recommend the smallest safe next experiment.

## Future milestones, not v1

- Live stream/webcam ingestion.
- Android companion app.
- Tablet capture workflow and tablet/browser viewer polish.
- Tablet on-device learned inference only after local PC runtime is proven and quantized/mobile runtime constraints are understood.
- Kinect for Windows plugin.
- Better measurement tools.
- Dense mesh generation.
- Better GLB conversion.
- Richer learned sidecar viewing: depth, confidence, mask, pointmap, and per-frame inspection.
- Packaged Windows installer.
