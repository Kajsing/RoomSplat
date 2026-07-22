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

### Hardened: frontend local API and viewer assumptions

- `frontend/src/api.ts` now reads `VITE_ROOMSPLAT_API_URL` / `VITE_BACKEND_URL` before falling back to `http://127.0.0.1:8000`.
- `frontend/src/components/ThreeViewer.tsx` renders listed 3D artifacts through Three.js, keeps debug reports as text, and labels splat fallback when GaussianSplats3D cannot read a file.
- `backend/app/services/debug_frame_cloud.py` limits Frame Room Cloud debug output to 50,000 points and writes metadata with `mode: debug` and `not_reconstruction: true`.
- Frame extraction jobs no longer need the frontend to echo an absolute `source_video` path back to the backend.

### Hardened: learned geometry bundle boundary

Milestone 9 readiness adds a metadata-only boundary for future LingBot-Map/VGGT-style adapters without adding a learned-model runtime dependency.

Controls:

- `metadata/geometry_bundle.json` is validated before it is returned by `GET /projects/{project_id}/geometry-bundle`.
- Declared source frames, primary artifacts, and required sidecars must resolve inside the project folder.
- Incomplete or invalid bundles are rejected and do not promote their declared primary PLY files into `predicted_point_cloud_ply` artifacts.
- Learned/predicted PLY outputs are labeled `predicted_point_cloud_ply`, distinct from COLMAP `point_cloud_ply` and Gaussian `splat_ply`.
- No automatic model/download/checkpoint behavior was added.

### Hardened: learned geometry import boundary

Milestone 10 adds `learned_geometry_preflight` and `import_learned_geometry` jobs. These jobs may read a user-provided local source folder outside the project, but they only write normalized outputs inside the selected RoomSplat project.

Controls:

- Source-relative `primary_ply` and sidecar paths reject absolute paths and `..` traversal before copy.
- `.complete.json` is required so half-written learned output folders are rejected.
- Declared frame sidecars such as `depth`, `confidence`, `mask`, and `points` must exist when completion metadata declares them.
- Imported primary PLYs are copied to `reconstruction/learned-point-cloud.ply` and only promoted after `metadata/geometry_bundle.json` validates.
- Copied sidecars are written under `metadata/learned/<adapter-slug>/`.
- Project frame mapping is validated against existing extracted frames; out-of-range frame indices fail the job.
- Imported learned geometry remains `is_reconstruction: false` and `not_reconstruction: true`.
- The import jobs do not run LingBot-Map, load checkpoints, download models, or start external viewers.

### Hardened: local learned runtime smoke boundary

Milestone 11 adds `learned_runtime_preflight` and `learned_runtime_smoke` jobs. These jobs can invoke a user-configured local adapter command, but only after preflight confirms the configured runtime boundary.

Controls:

- No automatic model or checkpoint download is implemented.
- Checkpoints must be user-supplied under `ROOMSPLAT_LEARNED_MODEL_ROOT`.
- Checkpoint paths are resolved under the model root and reject paths outside that root.
- Smoke execution requires `ROOMSPLAT_LEARNED_CHECKPOINT_SHA256` to match the checkpoint SHA-256.
- The runtime command is invoked with an argument list, not through a shell string.
- The checkpoint path is redacted from stored command diagnostics.
- Selected frames and runtime output folders are written under the selected project's ignored metadata folder.
- Successful runtime output is not promoted directly; it must pass the existing learned geometry import and geometry bundle validation.
- Blocked statuses such as `blocked_missing_dependencies`, `blocked_missing_checkpoint`, `blocked_untrusted_checkpoint`, and `blocked_insufficient_vram` do not create fake geometry artifacts.
- Frontend controls expose bounded max frames, frame step, image max size, precision, and CPU/offload flags without offering automatic downloads or public server exposure.

## Reviewed controls

- Project IDs are restricted to 32 lowercase hex characters before folder resolution.
- Project paths are checked against the configured data directory.
- Uploaded filenames are reduced to leaf names, sanitized, extension-checked, UUID-suffixed, and written under `input/`.
- Frame extraction source video paths must remain inside the project.
- ffmpeg is invoked with an argument list, not through a shell string.
- Artifact IDs decode to relative paths only; absolute and parent paths are rejected.
- Artifact listing and downloads only expose files that resolve inside the project folder.
- Learned geometry bundle paths are rejected if absolute, parent-relative, escaped through symlinks, missing when required, or inconsistent with declared artifact extensions.
- Learned geometry import source-relative paths are rejected if absolute, parent-relative, missing when declared, or inconsistent with the completed source-folder contract.
- Learned runtime checkpoint paths are restricted to the configured model root and must match the configured SHA-256 before execution.
- Learned runtime selected frames and output folders are contained under the selected project directory.
- Export creation writes only under `exports/` and records `real` versus `placeholder` status.
- Placeholder exports are explicit debug/workflow artifacts and are not labeled as real reconstruction.
- Frame Room Cloud outputs are explicit debug viewer artifacts and are not labeled as real reconstruction.
- `npm audit` was rerun after adding Three.js/GaussianSplats3D dependencies; Vite was upgraded to remove reported dev-server advisories.
- `.gitignore` excludes generated videos, frames, splats, exports, checkpoints, data folders, build outputs, virtualenvs, caches, and logs.

## Residual risks

- The app has no auth by design. Keep backend binding on `127.0.0.1` unless a future milestone adds authentication and exposure controls.
- Large or malformed media can still consume CPU/disk during parsing or ffmpeg extraction within the configured upload and timeout limits.
- API responses currently include local filesystem paths for operator transparency; this is acceptable for local-only v1 but should be revisited before LAN or shared use.
- Future real reconstruction adapters must preserve the same containment checks and avoid shell invocation.
- Future learned adapters must not use untrusted pickle checkpoints, automatic downloads, arbitrary output paths, or `0.0.0.0` viewer binding without a new security review. The current smoke path gates checkpoint use by location and SHA-256, but the external adapter runtime itself is still trusted local operator code.
- Learned geometry import currently trusts the local operator to choose an intended source folder; before exposing the backend beyond localhost, this external local read capability needs authentication and access controls.
- Real GLB conversion remains future work even though the browser can now render GLB scene artifacts when they exist.
- The current security baseline is focused and artifact-backed, not a complete production penetration test.

## Validation

Milestone validation should run:

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
git diff --check
git status --short
```
