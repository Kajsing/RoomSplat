# Real Reconstruction Preview v1

## Summary

Add the first real local reconstruction preview path for RoomSplat on Windows.

The current Frame Room Cloud is useful for viewer debugging, but it is not reconstruction. This goal adds a separate `reconstruct_point_cloud` job that uses a local COLMAP-backed flow to produce a real sparse point cloud artifact from extracted frames.

Gaussian Splatting remains the preferred longer-term direction, but this milestone should first establish camera/geometry reconstruction, dependency detection, metadata, artifact labeling, and viewer behavior for real 3D output.

## Scope

### Make debug frame planes harder to mistake for reconstruction

- Rename or relabel the UI artifact more clearly as debug frame planes when practical.
- Keep an always-visible warning for debug frame artifacts:
  - flat video frames placed in 3D,
  - not a reconstruction,
  - intended for viewer/debug inspection only.
- Make grid/point overlay controls clear enough that the debug artifact does not look like failed geometry.

### Add a real point cloud reconstruction job

- Add job type: `reconstruct_point_cloud`.
- Input: existing extracted frames under the project `frames/` folder.
- Use local COLMAP as the first Windows-native reconstruction backend:
  - feature extraction,
  - matching,
  - sparse reconstruction,
  - sparse point cloud export to PLY.
- Output:
  - `reconstruction/sparse-point-cloud.ply`,
  - `metadata/reconstruction.json`.
- Artifact label:
  - `point_cloud_ply`.
- Metadata must identify the output as real reconstruction, not debug or placeholder.

### Dependency handling

- Detect whether `colmap.exe` is available through PATH or configured path.
- If COLMAP is missing, fail the job with a clear, actionable setup message.
- Do not add COLMAP binaries to git.
- Do not introduce cloud upload, paid services, or Docker as a v1 requirement.
- Document the expected Windows setup path and environment variable if one is added.

### Viewer behavior for real point clouds

- Keep `debug_frame_cloud_ply` and `point_cloud_ply` visually and textually distinct.
- Fit camera to real point cloud bounding box.
- Show reconstruction stats where available:
  - point count,
  - bounding box,
  - source frame count,
  - registered frame count,
  - reconstruction status/quality notes.
- Keep existing color modes and point-size controls.
- Continue to support `splat_ply`, `mesh_glb`, and `debug_report` artifact switching.

### Workflow quality reporting

- Surface useful COLMAP result metadata in the backend and frontend:
  - number of input frames,
  - number of registered images/cameras,
  - number of sparse points,
  - whether the result is likely too sparse to inspect usefully.
- If reconstruction fails or registers too few frames, explain that clearly in job metadata/logs and UI.

## Tests

### Backend tests

- `reconstruct_point_cloud` rejects projects without extracted frames.
- Job fails cleanly when COLMAP is unavailable.
- Job uses path-contained project directories for inputs, intermediates, and outputs.
- Mocked/simulated COLMAP run writes:
  - `reconstruction/sparse-point-cloud.ply`,
  - `metadata/reconstruction.json`.
- Artifact listing labels the sparse PLY as `point_cloud_ply`.
- Metadata marks output as reconstruction and not debug/placeholder.
- Existing generated-data and artifact download containment tests remain passing.

### Pipeline tests

- Add a small COLMAP adapter or runner contract test with mocked subprocess output.
- Verify command construction does not allow user-controlled path injection.
- Verify PLY export discovery/parsing for the expected sparse output.

### Frontend/build tests

- Viewer distinguishes:
  - debug frame planes,
  - real point clouds,
  - splat PLY fallback,
  - GLB mesh,
  - debug report.
- Debug warnings appear only for debug artifacts.
- Reconstruction metadata/stats render when present.
- Vite build passes.

### Security checks

- No path traversal through COLMAP input, workspace, or export paths.
- No unsafe file serving outside the project directory.
- Generated reconstruction outputs remain ignored by git.
- No public exposure assumption changes; app remains local-only for v1.

## Manual/browser verification

- Start backend and frontend locally.
- Use the Objectron test project first.
- Extract frames.
- Run `reconstruct_point_cloud`.
- Open the viewer.
- Verify the selected artifact is a real `point_cloud_ply`, not debug frame planes.
- Verify canvas is nonblank with screenshot/pixel check.
- Test orbit, zoom, fit, reset, point size, color mode, artifact switching, and debug/reconstruction labels.
- Save a manual verification screenshot under ignored `data/manual-verification/`.

## Validation

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
npm --prefix frontend audit --audit-level=moderate
git diff --check
git status --short
```

If npm is not available in this shell, use the existing bundled Node/Vite fallback for frontend build and `pnpm dlx npm@latest` for audit.

## Documentation

Update:

- `README.md`
- `ARCHITECTURE.md`
- `docs/project-format.md`
- `docs/validation.md`
- `DOCUMENTATION.md`
- `.logs/YYYY-MM-DD-real-reconstruction-preview-v1.md`

Document clearly:

- COLMAP setup and detection on Windows.
- Debug frame planes are not reconstruction.
- `reconstruct_point_cloud` is the first real reconstruction preview.
- Real Gaussian Splatting training remains a later milestone.
- Remaining dependency and quality limitations.

## Acceptance Criteria

- A new `reconstruct_point_cloud` job can run from extracted frames.
- Missing COLMAP produces a clear setup/dependency error.
- A mocked or real local COLMAP run can produce a path-contained sparse point cloud PLY.
- Artifact listing exposes the output as `point_cloud_ply`.
- Metadata distinguishes real reconstruction from debug artifacts and placeholders.
- The browser viewer can inspect the real point cloud separately from debug frame planes.
- Tests cover dependency handling, path containment, metadata, artifact labeling, and viewer mode distinction.
- Build, tests, audit, diff check, and status checks pass.
- Commit and push after completion.
