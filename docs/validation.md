# Validation

Use the milestone-specific commands in `PLAN.md` as the source of truth.

## Current baseline

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

Optional frontend helper check in the bundled Node runtime:

```bash
node --experimental-strip-types --test frontend/tests/*.test.ts
```

## Expected smoke path

1. Create a local project.
2. Import a tiny video.
3. Create a frame extraction job.
4. Poll until job status is `succeeded` or `failed`.
5. Verify `metadata/video_import.json`, `metadata/frame_extraction.json`, `metadata/jobs/<job-id>.json`, `metadata/jobs/<job-id>.log`, and `frames/frame_*.png`.
6. Create a reconstruction-spike job.
7. Verify `metadata/reconstruction_spike.json` records dependency readiness and output contracts.
8. Create a debug-frame-cloud job with custom params such as `max_points`, `frame_step`, `arc_degrees`, and `plane_width`.
9. Verify `reconstruction/debug-frame-room.ply` and `metadata/debug_frame_cloud.json` exist and are marked debug/not reconstruction.
10. Verify `metadata/debug_frame_cloud.json` records params, sampled point count, source frame count, selected frame count, and `frame_planes[]`.
11. List artifacts through `GET /projects/{project_id}/artifacts`.
12. Load supported artifacts in the viewer or show explicit debug/unsupported states.
13. Verify the Three.js canvas is nonblank for `debug_frame_cloud_ply` and that debug report artifact switching still works.
14. Verify large-view mode, camera presets, grid/axes toggles, point size, color mode, frame markers, screenshot capture, and not-reconstruction warning.
15. Create exports through `POST /projects/{project_id}/exports`.
16. Verify `metadata/exports/<export-id>.json` records source artifact, format, generated time, artifact label, and `real`/`placeholder` status.
17. Download the exported file through the artifact download URL.
18. Confirm the backend is bound to `127.0.0.1` for local v1 use.
19. Confirm generated data remains ignored by Git.

## Validation principle

The app must not present placeholder reconstruction output as real reconstruction. Missing external reconstruction dependencies should produce clear, actionable messages.

Security baseline checks should cover path containment for project IDs, uploads, frame extraction sources, job paths, artifact IDs, artifact listing/downloads, and export outputs.
