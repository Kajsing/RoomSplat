# local-3d-room-mapper

Local Windows-first web app for video-to-3D reconstruction using a Gaussian Splatting / NeRF-style pipeline.

The first version focuses on the local engine: import a video, extract frames, run or spike a local reconstruction path, inspect the result, and export `.ply` / `.glb` artifacts.

## What works now

- FastAPI backend with `GET /health`.
- Local project storage with `GET /projects` and `POST /projects`.
- Video upload into project `input/` folders.
- Deterministic frame extraction into project `frames/` folders.
- Local background jobs for frame extraction and reconstruction-spike orchestration.
- Vite + React frontend displaying backend health, create/list projects, video upload, and job status.

## What it does not do yet

- No real Gaussian Splatting / NeRF training is integrated yet; the current reconstruction path is a dependency/readiness spike.
- General MP4/MOV extraction requires `ffmpeg` on PATH or `ROOMSPLAT_FFMPEG_PATH`.
- No live phone/webcam streaming yet.
- No native Android app.
- No cloud processing or user accounts.
- No construction-grade measurement guarantees.

## Start backend

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .
uvicorn app.main:app --app-dir backend --reload
```

## Start frontend

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

## Run tests

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

## Generated data

Generated videos, frames, reconstruction outputs, splats, checkpoints, and exports belong under `data/` or per-project output folders and must not be committed.

## Documentation map

- `SPEC.yaml` - product and technical requirements.
- `PLAN.md` - milestone order, acceptance criteria, and validation commands.
- `IMPLEMENT.md` - implementation runbook.
- `ARCHITECTURE.md` - system boundaries and data flow.
- `DOCUMENTATION.md` - current status, decisions, known issues, and commands run.
- `docs/archive/roomsplat-dev-doc.md` - original handoff specification kept as historical reference.
