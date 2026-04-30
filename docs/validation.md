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
4. Create an extraction or reconstruction job.
5. Produce a clearly labeled placeholder or real artifact, depending on milestone.
6. Load the artifact in the viewer.
7. Export `.ply` and `.glb` files when supported.

## Validation principle

The app must not present placeholder reconstruction output as real reconstruction. Missing external reconstruction dependencies should produce clear, actionable messages.
