# local-3d-room-mapper

Local Windows-first web app for video-to-3D reconstruction pipeline scaffolding.

## What works now
- FastAPI backend with `GET /health`.
- Vite + React frontend displaying backend health.

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
