# Usable 3D Viewer Preview

## Summary

Build Frame Room Cloud and the Three.js viewer into a practical debug/inspection version, so RoomSplat has a stable visual middle step before real Gaussian Splatting reconstruction is integrated.

Frame Room Cloud remains debug-only. It must never be described as room reconstruction.

## Scope

### Improve Frame Room Cloud generation

- Add metadata for frame planes:
  - frame index,
  - source frame,
  - plane position,
  - plane angle,
  - point count.
- Make spacing and arc easier to inspect:
  - stable radius,
  - readable frame gap,
  - auto-scale for frame count.
- Add job params:
  - `max_points`,
  - `frame_step`,
  - `arc_degrees`,
  - `plane_width`.
- Preserve deterministic output, max point cap, and `not_reconstruction: true`.

### Improve the browser viewer

- Add fullscreen or large-view mode.
- Add camera presets:
  - front,
  - side,
  - top,
  - default orbit.
- Add artifact stats:
  - artifact type,
  - point count when known,
  - file size,
  - debug/reconstruction warning.
- Add optional frame-plane labels or markers when metadata exists.
- Improve empty/error states for:
  - splat fallback,
  - invalid PLY,
  - invalid/empty GLB.
- Add a local screenshot button for the viewer canvas.

### Prepare the splat-first workflow

- Keep GaussianSplats3D as the primary `splat_ply` loader.
- Improve fallback diagnostics when a splat PLY is displayed as a point cloud.
- Document the expected real splat artifact contract:
  - file naming,
  - artifact label,
  - metadata,
  - viewer assumptions.

## Tests

### Backend tests

- `debug_frame_cloud` accepts supported params and records them in metadata.
- Rejects invalid params:
  - `max_points` over cap,
  - `frame_step < 1`,
  - invalid `arc_degrees`,
  - invalid `plane_width`.
- Same input and params produce deterministic PLY output, excluding timestamp metadata.
- Metadata includes frame plane records.
- Artifact listing still labels `debug-frame-room.ply` as `debug_frame_cloud_ply`.
- Path containment tests remain in place.
- `GET /projects/{project_id}/frames/extraction` returns frame metadata and 404s when missing.

### Frontend/build tests

- Vite build passes with viewer modes:
  - `debug_frame_cloud_ply`,
  - `point_cloud_ply`,
  - `splat_ply`,
  - `mesh_glb`,
  - `debug_report`.
- Add focused helper tests if viewer helpers are extracted:
  - artifact label formatting,
  - artifact stats formatting,
  - supported-mode checks.

### Manual/browser tests

- Start backend and frontend.
- Use the Objectron test project.
- Create a debug preview with custom params.
- Verify:
  - WebGL canvas is nonblank by screenshot/pixel check,
  - fullscreen opens and closes,
  - camera presets change the view,
  - grid and axes toggles work,
  - point size and color mode work,
  - artifact switching works between debug report and Frame Room Cloud,
  - screenshot button creates an image,
  - warning still says this is not reconstruction.

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
- `.logs/YYYY-MM-DD-usable-viewer-preview.md`

Document clearly:

- Frame Room Cloud is debug/inspection only.
- Real reconstruction/splat training remains a later milestone.
- Supported debug preview job params and their limits.

## Acceptance Criteria

- A user can create a Frame Room Cloud from extracted frames and inspect it comfortably in the browser.
- Viewer feels like a useful tool rather than only a proof of concept.
- All debug artifacts are clearly labeled as not reconstruction.
- Tests cover generator params, determinism, limits, metadata, API flow, and artifact labeling.
- Build, tests, audit, diff check, and status checks pass.
- Commit and push after completion.
