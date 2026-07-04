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
8. Produce a clearly labeled placeholder or real artifact, depending on milestone.
9. Load the artifact in the viewer.
10. Export `.ply` and `.glb` files when supported.

## Validation principle

The app must not present placeholder reconstruction output as real reconstruction. Missing external reconstruction dependencies should produce clear, actionable messages.
