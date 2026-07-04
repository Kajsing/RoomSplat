# Usable 3D Viewer Preview

Date: 2026-07-04

Goal: make Frame Room Cloud and the Three.js browser viewer useful for local debug/inspection while preserving the not-reconstruction boundary.

## Completed

- Added Frame Room Cloud job params:
  - `max_points`
  - `frame_step`
  - `arc_degrees`
  - `plane_width`
- Added strict backend validation for debug preview params.
- Changed Frame Room Cloud sampling so selected frames receive deterministic plane records and point budgets.
- Added `frame_planes[]` metadata with source frame, plane position, angle, point count, image size, and plane size.
- Added `GET /projects/{project_id}/debug-frame-cloud` for viewer metadata.
- Added frontend controls for creating debug previews with custom params.
- Added Three.js viewer features:
  - large-view mode,
  - default/front/side/top camera presets,
  - artifact stats,
  - optional frame markers,
  - screenshot capture,
  - point-size stepper buttons,
  - improved PLY/GLB empty-state errors,
  - clearer GaussianSplats3D fallback diagnostics.
- Added artifact URL cache-busting from `modified_at` so regenerating `debug-frame-room.ply` does not leave the viewer showing stale cached geometry.
- Added frontend helper tests for artifact labels, supported viewer modes, and byte formatting.

## Tests added or adjusted

- Backend tests cover:
  - supported params recorded in metadata,
  - invalid `max_points`, `frame_step`, `arc_degrees`, and `plane_width`,
  - deterministic PLY output excluding timestamp metadata,
  - frame-plane metadata,
  - debug metadata endpoint,
  - artifact label preservation,
  - existing path containment.
- Frontend helper tests cover:
  - artifact label formatting,
  - Three.js-supported artifact modes,
  - stats byte formatting.

## Assumptions

- Frame markers are enough for the first version of frame-plane labels; text labels can be added later if needed.
- Large-view mode is acceptable for this milestone instead of using the browser fullscreen API.
- Real splat reconstruction remains future work; this milestone only improves inspection and fallback behavior.

## Remaining risks

- The frontend bundle remains large because Three.js and GaussianSplats3D are loaded in the app bundle.
- Real `splat_ply` compatibility still depends on future reconstruction output matching what GaussianSplats3D can parse.
- Screenshot capture creates a local canvas data URL and now shows a UI status; browser automation did not expose a download event for the data URL.

## Browser smoke

- Used Objectron project `9522ce63dbfc454fb638fae38375863c`.
- Created a debug preview from the UI with:
  - `max_points=12000`
  - `frame_step=2`
  - `arc_degrees=90`
  - `plane_width=1.8`
- Backend metadata recorded 4 frame planes and 11,656 sampled points.
- Verified viewer stats matched the regenerated PLY after cache-busting.
- Verified large-view mode, camera presets, grid/axes/frame marker toggles, point-size stepper, color mode, screenshot status, artifact switching, and not-reconstruction warning.
- Saved ignored screenshot at `data/manual-verification/usable-viewer-preview.png`.
- Canvas pixel crop was nonblank: 44 unique colors, non-background ratio 1.0.

## Final validation

- `python -m pytest backend/tests pipeline/tests` passed, 51 tests.
- `node --experimental-strip-types --test frontend/tests/*.test.ts` passed, 4 tests.
- Frontend Vite build passed with the known Three.js/GaussianSplats3D chunk-size warning.
- `npm audit --audit-level=moderate` passed with 0 vulnerabilities.
- `git diff --check` passed with line-ending warnings only.
- Generated Objectron debug outputs and browser screenshots remained under ignored `data/`.
