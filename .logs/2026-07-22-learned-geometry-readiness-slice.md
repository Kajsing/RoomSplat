# Learned geometry readiness slice

Date: 2026-07-22

## Summary

Implemented a substantial Milestone 9 readiness slice for learned geometry / feed-forward reconstruction outputs, inspired by the local LingBot-Map reference copy at `C:\project\lingbot-map`.

No LingBot-Map runtime, checkpoint loader, automatic model download, or learned-model dependency was added.

## Completed

- Added `backend/app/services/geometry_bundle.py`.
- Added pipeline-side geometry bundle contract helpers in `pipeline/adapters/base.py`.
- Added `metadata/geometry_bundle.json` validation contract with:
  - schema version,
  - source adapter,
  - frame count and frame index map,
  - camera poses,
  - intrinsics,
  - trajectory,
  - depth/confidence/mask/pointmap capability declarations,
  - primary artifacts,
  - sidecars,
  - quality notes,
  - warnings,
  - completion status,
  - generated-data rules,
  - strict project path containment.
- Added `GET /projects/{project_id}/geometry-bundle`.
- Added artifact types `predicted_point_cloud_ply` and `learned_geometry_bundle`.
- Artifact listing now labels bundle-declared learned PLYs as `predicted_point_cloud_ply`.
- Invalid or incomplete bundles do not promote declared learned PLYs into the artifact list.
- Learned bundles must keep `is_reconstruction: false` and `not_reconstruction: true` until a later adapter explicitly promotes or converts them.
- Frontend API/types, viewer helpers, export controls, and Three.js point viewer path now understand predicted point clouds.
- Added backend tests for valid bundle, artifact labeling, incomplete bundle rejection, escaped sidecar rejection, and missing primary artifact rejection.
- Added pipeline tests for learned geometry expected outputs, missing manifest rejection, escaped path rejection, and non-PLY predicted output rejection.
- Updated project format, validation, security baseline, risks, and documentation notes.

## Validation

Focused checks passed:

```bash
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests/test_geometry_bundle.py backend/tests/test_artifacts.py backend/tests/test_exports.py
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests pipeline/tests
C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts
C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build
git diff --check
```

The Vite build still emits the existing large chunk warning.

## Remaining risks

- Future learned adapters still need checkpoint safety, checksum/allowlist policy, isolated env setup, and no-auto-download defaults.
- Depth/confidence sidecar readers are not implemented yet.
- Viewer confidence filtering, current/all-frame mode, frame selection, and clickable learned camera controls remain future UI work.
