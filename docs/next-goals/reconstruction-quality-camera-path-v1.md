# Reconstruction Quality + Camera Path v1

## Summary

Improve the COLMAP sparse reconstruction workflow so early results are easier to understand and compare.

Real sparse point clouds are now working, but the viewer only shows points. This goal adds COLMAP camera/path metadata and viewer controls so a user can see where the cameras were, how the camera moved, how strong the reconstruction was, and how real reconstruction artifacts differ from debug frame planes and placeholders.

## Scope

### Make sparse reconstruction easier to inspect

- Parse COLMAP camera/image outputs from the text model:
  - `cameras.txt`
  - `images.txt`
  - `points3D.txt`
- Store camera/image metadata in `metadata/reconstruction.json`.
- Include:
  - registered image count,
  - camera poses,
  - camera centers,
  - camera names/source frames,
  - trajectory bounds,
  - sparse point count,
  - reconstruction quality status.
- Preserve the existing `point_cloud_ply` artifact contract.

### Add camera/path visualization to the Three.js viewer

- Show camera positions or frustums for real `point_cloud_ply` reconstructions when metadata exists.
- Show a camera trajectory/path line.
- Add toggles:
  - points,
  - cameras,
  - path,
  - grid,
  - axes.
- Keep debug frame-plane markers separate from real reconstruction cameras.
- Keep fit/reset/camera presets working when cameras/path overlays exist.

### Improve reconstruction controls

- Add practical reconstruction params or presets in the UI:
  - quick,
  - balanced,
  - detail.
- Params may include:
  - frame stride,
  - max frames,
  - matcher: `exhaustive` or `sequential`.
- Document runtime/quality tradeoffs.
- Avoid silently changing already extracted frames unless the user starts a new extraction/reconstruction flow.

### Improve artifact ordering and labeling

- Prioritize real artifacts above debug/placeholder artifacts:
  - real `point_cloud_ply`,
  - future `splat_ply`,
  - `mesh_glb`,
  - debug frame planes,
  - debug reports,
  - placeholder exports.
- Make placeholder exports visually lower priority and clearly labeled.
- Keep `debug_frame_cloud_ply` labeled as debug frame planes, not reconstruction.

### Validate across available test videos

Use the current ignored local samples:

- Objectron cup
- Objectron chair
- Objectron shoe

For each sample, record:

- video path,
- extraction stride/max frames,
- extracted frame count,
- registered frame count,
- sparse/PLY point count,
- quality status,
- browser smoke result where practical.

## Tests

### Backend/pipeline tests

- Parser reads COLMAP `images.txt`, `cameras.txt`, and `points3D.txt`.
- Camera centers/poses are deterministic for known tiny text fixtures.
- Reconstruction metadata includes camera/path records when text model data exists.
- Quality status handles:
  - good/inspectable result,
  - too few registered frames,
  - too few points.
- Path containment remains enforced for frames, workspace, metadata, and output artifacts.
- Artifact listing orders real artifacts before debug/placeholder artifacts.

### Frontend/build tests

- Viewer helper tests cover artifact priority/order and labels.
- Reconstruction metadata types include cameras/path.
- Viewer builds with camera/path toggles.
- Debug frame-plane warnings remain separate from real reconstruction notices.
- Vite build passes.

### Manual/browser tests

- Start backend and frontend.
- Select the cup/chair/shoe projects or create them from downloaded sample videos.
- Run/inspect real point-cloud reconstruction.
- Verify:
  - point cloud is visible,
  - camera positions/frustums are visible,
  - camera path is visible,
  - points/cameras/path toggles work,
  - debug frame planes still show not-reconstruction warning,
  - placeholder exports are clearly lower-priority,
  - screenshot/pixel check is nonblank.

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
- `.logs/YYYY-MM-DD-reconstruction-quality-camera-path-v1.md`

Document clearly:

- sparse point cloud vs camera path vs Gaussian splat,
- how to interpret registered frames and point counts,
- quick/balanced/detail tradeoffs,
- cup/chair/shoe validation results,
- remaining limitations before real splat training.

## Acceptance Criteria

- Real COLMAP reconstruction metadata includes camera/image/path data.
- Three.js viewer can display real point clouds with camera/path overlays.
- Viewer toggles distinguish points, cameras, path, grid, axes, and debug frame markers.
- Artifact ordering and labeling make real/debug/placeholder status obvious.
- Cup/chair/shoe samples have recorded reconstruction results.
- Tests cover parser, metadata, quality status, artifact ordering, labels, and build.
- Full validation, browser smoke, diff check, and status checks pass.
- Commit and push after completion.
