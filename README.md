# local-3d-room-mapper

Local Windows-first web app for video-to-3D reconstruction using a Gaussian Splatting / NeRF-oriented pipeline.

## Project docs
- Primary planning/spec files live at repo root: `AGENTS.md`, `PLAN.md`, `IMPLEMENT.md`, `DOCUMENTATION.md`, `SPEC.yaml`, `ARCHITECTURE.md`.
- Original handoff document is archived at `docs/archive/roomsplat-dev-doc.md`.

## What works now
- FastAPI backend with `GET /health`.
- Vite + React frontend displaying backend health.

## Start backend
```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -e .[dev]
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
