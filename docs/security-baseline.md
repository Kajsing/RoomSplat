# Security Baseline

Date: 2026-07-04

Scope: focused Milestone 8 baseline for the local Windows v1 app. This is not a production penetration test. It covers the current FastAPI routes/services, local worker, artifact/export boundaries, pipeline scripts, frontend API assumptions, generated-data rules, and documentation around local-only operation.

## Threat model summary

- RoomSplat is local-only by design for v1 and has no authentication.
- The local filesystem under the configured data directory is the primary asset.
- Uploaded media, filenames, route params, job params, artifact IDs, and export requests are untrusted API inputs.
- The frontend is a client, not a security boundary.
- If the backend is exposed beyond localhost, anyone who can reach it can operate the app.

## Findings and fixes

### Fixed: reconstruction job `frames_dir` could point outside the project

The reconstruction-spike worker previously accepted a `frames_dir` job parameter and resolved it without checking that it stayed inside the project folder.

Fix:

- `backend/app/workers/local_worker.py` now resolves relative paths under the project and rejects paths outside the project.
- `backend/tests/test_jobs.py` covers the rejected outside-project case.

### Fixed: upload body size had no configured limit

The upload route read the full request body before import validation, which could create avoidable local memory pressure.

Fix:

- `backend/app/config.py` now supports `ROOMSPLAT_MAX_UPLOAD_MB` / `MAX_UPLOAD_MB`.
- `backend/app/api/routes_uploads.py` rejects oversized uploads with HTTP 413 while streaming the request body.
- `.env.example` documents the limit.
- `backend/tests/test_video_import.py` covers the configured limit.

### Fixed: artifact listing could expose symlink metadata

Artifact downloads already resolved paths and rejected escapes, but listing used `path.is_file()` and `stat()` before a resolved containment check. A symlink under `reconstruction/` or `exports/` could expose target metadata such as name, size, or modified time even though download was blocked.

Fix:

- `backend/app/services/export_service.py` now checks resolved containment before listing an artifact.
- `backend/tests/test_artifacts.py` covers escaped symlinks when the Windows environment permits symlink creation.

### Fixed: ffmpeg extraction had no timeout

Frame extraction invoked ffmpeg with an argument list, so shell injection was not observed, but long-running media processing could hang a worker.

Fix:

- `backend/app/config.py` now supports `ROOMSPLAT_FFMPEG_TIMEOUT_SECONDS`.
- `backend/app/services/frame_extraction.py` passes a timeout to `subprocess.run`.
- Timeout failures are reported as frame extraction errors.
- `backend/tests/test_video_import.py` covers timeout handling.

### Hardened: frontend local API and preview assumptions

- `frontend/src/api.ts` now reads `VITE_ROOMSPLAT_API_URL` / `VITE_BACKEND_URL` before falling back to `http://127.0.0.1:8000`.
- `frontend/src/viewer/pointCloudViewer.ts` limits in-browser ASCII PLY preview to 50,000 vertices and tells users to download larger artifacts.
- Frame extraction jobs no longer need the frontend to echo an absolute `source_video` path back to the backend.

## Reviewed controls

- Project IDs are restricted to 32 lowercase hex characters before folder resolution.
- Project paths are checked against the configured data directory.
- Uploaded filenames are reduced to leaf names, sanitized, extension-checked, UUID-suffixed, and written under `input/`.
- Frame extraction source video paths must remain inside the project.
- ffmpeg is invoked with an argument list, not through a shell string.
- Artifact IDs decode to relative paths only; absolute and parent paths are rejected.
- Artifact listing and downloads only expose files that resolve inside the project folder.
- Export creation writes only under `exports/` and records `real` versus `placeholder` status.
- Placeholder exports are explicit debug/workflow artifacts and are not labeled as real reconstruction.
- `.gitignore` excludes generated videos, frames, splats, exports, checkpoints, data folders, build outputs, virtualenvs, caches, and logs.

## Residual risks

- The app has no auth by design. Keep backend binding on `127.0.0.1` unless a future milestone adds authentication and exposure controls.
- Large or malformed media can still consume CPU/disk during parsing or ffmpeg extraction within the configured upload and timeout limits.
- API responses currently include local filesystem paths for operator transparency; this is acceptable for local-only v1 but should be revisited before LAN or shared use.
- Future real reconstruction adapters must preserve the same containment checks and avoid shell invocation.
- Full in-browser GLB rendering and real GLB conversion remain future work.
- The current security baseline is focused and artifact-backed, not a complete production penetration test.

## Validation

Milestone validation should run:

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
git diff --check
git status --short
```
