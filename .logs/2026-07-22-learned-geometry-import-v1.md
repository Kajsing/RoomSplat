# Learned geometry import/preflight v1

Date: 2026-07-22

## Summary

Implemented a RoomSplat-native import/preflight flow for completed local learned-geometry output folders.

The work is inspired by the local LingBot-Map reference copy at `C:\project\lingbot-map`, especially its BSS-style output layout:

- `.complete.json`
- global `points.ply`
- `traj.txt`
- `intrinsics.txt`
- `sampling.json`
- per-frame `depth/`, `confidence/`, `mask/`, and `points/` sidecar folders

No LingBot-Map runtime, VGGT runtime, checkpoint loader, model download, cloud dependency, or required learned runtime was added.

## Completed

- Added `pipeline/adapters/learned_geometry_import.py`.
- Added pipeline helpers for:
  - source-folder inspection,
  - completion metadata validation,
  - primary PLY validation,
  - declared sidecar validation,
  - expected sidecar reporting,
  - adapter assessment output contracts.
- Added `backend/app/services/learned_geometry_import.py`.
- Added job types:
  - `learned_geometry_preflight`
  - `import_learned_geometry`
- `learned_geometry_preflight` validates project extracted frames and a completed local source folder without copying outputs.
- `import_learned_geometry` copies:
  - primary PLY to `reconstruction/learned-point-cloud.ply`,
  - sidecars to `metadata/learned/<adapter-slug>/`,
  - bundle metadata to `metadata/geometry_bundle.json`.
- Imported PLYs are promoted only as `predicted_point_cloud_ply`.
- Imported geometry stays `is_reconstruction: false` and `not_reconstruction: true`.
- Added frontend job controls for learned source folder, adapter label, primary PLY, preflight, and import.
- Added frontend metadata inspection for `learned_geometry_bundle`.
- Updated README, PLAN, ARCHITECTURE, DOCUMENTATION, project format, validation, security baseline, and pipeline docs.

## Validation

Focused checks run during implementation:

```bash
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests/test_learned_geometry_import.py backend/tests/test_geometry_bundle.py
$env:PYTHONPATH='backend'; py -3.12 -m pytest pipeline/tests/test_learned_geometry_source_import.py pipeline/tests/test_learned_geometry_contract.py
C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts
C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build
```

Final validation:

```bash
$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests pipeline/tests
C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts
C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build
git diff --check
```

Results:

- Backend/pipeline: 108 passed.
- Frontend helper tests: 12 passed.
- Frontend build: passed with existing large chunk warning.
- `git diff --check`: passed with Windows line-ending warnings only.

## Remaining risks

- No file-count or byte-size cap is enforced for large learned sidecar folders yet.
- The backend reads from a user-provided local source folder for this import flow; keep v1 localhost-only and unauthenticated.
- Future learned runtimes still need isolated environment setup, checksum/allowlist policy, explicit no-auto-download defaults, and checkpoint safety review.
- Viewer support for depth/confidence/pointmap sidecars remains metadata-only; filtering and frame selection are future UI work.
