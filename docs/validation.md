# Validation

Use the milestone-specific commands in `PLAN.md` as the source of truth.

## Current baseline

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

## Expected smoke path

1. Create a local project.
2. Import a tiny video.
3. Create a frame extraction job.
4. Poll until job status is `succeeded` or `failed`.
5. Verify `metadata/video_import.json`, `metadata/frame_extraction.json`, `metadata/jobs/<job-id>.json`, `metadata/jobs/<job-id>.log`, and `frames/frame_*.png`.
6. Create a reconstruction-spike job.
7. Verify `metadata/reconstruction_spike.json` records dependency readiness and output contracts.
8. List artifacts through `GET /projects/{project_id}/artifacts`.
9. Load supported artifacts in the viewer or show explicit debug/unsupported states.
10. Create exports through `POST /projects/{project_id}/exports`.
11. Verify `metadata/exports/<export-id>.json` records source artifact, format, generated time, artifact label, and `real`/`placeholder` status.
12. Download the exported file through the artifact download URL.

## Validation principle

The app must not present placeholder reconstruction output as real reconstruction. Missing external reconstruction dependencies should produce clear, actionable messages.
