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
