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
3. Extract frames.
4. Verify `metadata/video_import.json`, `metadata/frame_extraction.json`, and `frames/frame_*.png`.
5. Create an extraction or reconstruction job when Milestone 5 exists.
6. Produce a clearly labeled placeholder or real artifact, depending on milestone.
7. Load the artifact in the viewer.
8. Export `.ply` and `.glb` files when supported.

## Validation principle

The app must not present placeholder reconstruction output as real reconstruction. Missing external reconstruction dependencies should produce clear, actionable messages.
