# local-3d-room-mapper

Local Windows-first web app for video-to-3D reconstruction using a Gaussian Splatting / NeRF-style pipeline.

The first version focuses on the local engine: import a video, extract frames, run or spike a local reconstruction path, inspect the result, and export `.ply` / `.glb` artifacts.

Security model: v1 is a local single-user app. Bind the backend to `127.0.0.1`; do not expose it to an untrusted LAN or the public internet because there is no authentication yet.

## What works now

- FastAPI backend with `GET /health`.
- Local project storage with `GET /projects` and `POST /projects`.
- Video upload into project `input/` folders.
- Deterministic frame extraction into project `frames/` folders.
- Local background jobs for frame extraction, reconstruction-spike orchestration, debug frame planes, and real sparse point-cloud reconstruction.
- Artifact discovery/download APIs with explicit labels for debug frame clouds, point clouds, splats, GLB, and debug reports.
- Browser Three.js viewer with orbit/inspect controls, large-view mode, camera presets, stats, screenshot capture, frame markers for debug frame clouds, point cloud PLY, splat PLY fallback, and GLB scenes.
- Export APIs and UI controls for `.ply` / `.glb` outputs, including explicit placeholder labels for debug exports.
- Vite + React frontend displaying backend health, create/list projects, video upload, job status, and artifact viewer states.
- Focused security baseline docs and tests for path containment, upload limits, artifact downloads, and local-only assumptions.

## What it does not do yet

- No real Gaussian Splatting / NeRF training is integrated yet; the current reconstruction path is a dependency/readiness spike.
- Placeholder exports can be created from the reconstruction spike report for UI/workflow testing, but they are labeled as placeholders and are not real reconstruction.
- Real Gaussian Splatting reconstruction is still future work; debug frame planes are sampled from extracted frames for viewer/debug testing only.
- Real sparse point-cloud reconstruction requires local COLMAP.
- General MP4/MOV extraction requires `ffmpeg` on PATH or `ROOMSPLAT_FFMPEG_PATH`.
- No live phone/webcam streaming yet.
- No native Android app.
- No cloud processing or user accounts.
- No construction-grade measurement guarantees.

## Windows prerequisites

- Python 3.12 recommended.
- Node.js 20+ and npm.
- Git.
- Optional for MP4/MOV/AVI/MKV/WebM extraction: ffmpeg on `PATH` or configured with `ROOMSPLAT_FFMPEG_PATH`.
- Optional for real sparse point-cloud reconstruction: COLMAP on `PATH` or configured with `ROOMSPLAT_COLMAP_PATH`.
- Optional future splat tooling: pycolmap, Nerfstudio/Splatfacto, gsplat, PyTorch/CUDA, and Open3D.

GIF fixtures and tests work without ffmpeg. Real reconstruction training is not integrated yet.

## Configure

Copy `.env.example` to `.env` if you want local overrides. Important defaults:

- `ROOMSPLAT_DATA_DIR=./data`
- `ROOMSPLAT_MAX_UPLOAD_MB=2048`
- `ROOMSPLAT_FFMPEG_TIMEOUT_SECONDS=1800`
- `ROOMSPLAT_COLMAP_PATH=` optional full path to `colmap.exe`
- `VITE_ROOMSPLAT_API_URL=http://127.0.0.1:8000`

Keep generated project data under `data/` or another ignored local folder.

## Install backend

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Start backend

```bash
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

## Install frontend

```bash
npm --prefix frontend install
```

## Start frontend

```bash
npm --prefix frontend run dev
```

Open the Vite URL shown in the terminal, usually `http://127.0.0.1:5173`.

## Workflow

1. Create a project.
2. Upload a short video or GIF.
3. Extract frames through the local job flow.
4. Create debug frame planes if you want a quick flat-frame-in-3D artifact for testing viewer orientation and controls. Optional parameters are `max_points`, `frame_step`, `arc_degrees`, and `plane_width`.
5. Run point cloud reconstruction to create a real COLMAP sparse point cloud at `reconstruction/sparse-point-cloud.ply`.
6. Run the reconstruction spike to check longer-term splat dependency readiness.
7. Inspect listed artifacts/debug reports in the browser viewer.
8. Export `.ply` or `.glb` artifacts when available.

Placeholder exports are allowed only for workflow/debug testing and are labeled as placeholders.
Debug frame plane artifacts are also debug-only and must not be described as reconstruction output.

If COLMAP is not installed, the point-cloud reconstruction job fails with setup guidance instead of writing fake output.

## Run tests

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

If npm is not available in your shell but Node is, use the direct Vite CLI from `frontend/` as a fallback:

```bash
node node_modules/vite/bin/vite.js build
```

## Generated data

Generated videos, frames, reconstruction outputs, splats, checkpoints, and exports belong under `data/` or per-project output folders and must not be committed.

## Capture and output notes

- Start with short, slow clips of a small room or object.
- Prefer bright, even lighting and overlapping camera paths.
- Avoid fast pans, reflective surfaces, transparent objects, and textureless walls while testing.
- `point_cloud_ply` is a conventional point cloud.
- `debug_frame_cloud_ply` is a deterministic viewer/debug point cloud sampled from flat extracted frames and placed in 3D; it is not a reconstruction.
- `reconstruction/sparse-point-cloud.ply` is a real COLMAP sparse `point_cloud_ply` artifact when point-cloud reconstruction succeeds.
- `splat_ply` is Gaussian splat data stored in a PLY-like format, not a conventional point cloud.
- `mesh_glb` is a portable scene/mesh container only when a real conversion path exists.
- Large PLY files should be downloaded for full inspection; the debug frame planes generator caps output at 50,000 points.
- Debug frame plane metadata records sampled frame planes, point counts, params, and `not_reconstruction: true`.
- Real sparse reconstruction metadata is written to `metadata/reconstruction.json` with COLMAP workspace, input frame count, registered frame count, point count, and quality notes.

## Documentation map

- `SPEC.yaml` - product and technical requirements.
- `PLAN.md` - milestone order, acceptance criteria, and validation commands.
- `IMPLEMENT.md` - implementation runbook.
- `ARCHITECTURE.md` - system boundaries and data flow.
- `DOCUMENTATION.md` - current status, decisions, known issues, and commands run.
- `docs/capture-guide.md` - video capture tips.
- `docs/project-format.md` - project storage, artifact labels, and export metadata.
- `docs/security-baseline.md` - Milestone 8 focused security baseline.
- `docs/risks.md` - current technical risks and mitigations.
- `docs/archive/roomsplat-dev-doc.md` - original handoff specification kept as historical reference.
