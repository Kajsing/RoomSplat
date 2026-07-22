# Learned Geometry Adapter Readiness

## Summary

Prepare RoomSplat for optional feed-forward / learned reconstruction adapters inspired by `C:\project\lingbot-map`, without making LingBot-Map or any other research stack a core dependency.

This goal is about contracts first: make RoomSplat able to receive and describe predicted geometry bundles containing camera poses, intrinsics, trajectory, depth/confidence availability, pointmap-style geometry, point clouds, and sidecar metadata.

## Key Changes

- Add a RoomSplat-native geometry bundle contract under project `metadata/`.
- Keep the contract adapter-neutral and independent of COLMAP, Nerfstudio, LingBot-Map, or VGGT internals.
- Define artifact labels and descriptions for learned/predicted geometry so it is not confused with Gaussian splats, COLMAP point clouds, meshes, or metric scans.
- Plan viewer controls for confidence filtering, frame selection, current/all frame display, clickable cameras/frustums, camera downsampling, and trajectory inspection.
- Add safety rules for future learned adapters:
  - no automatic checkpoint or dataset downloads by default,
  - user-supplied model paths,
  - checksum or allowlist before loading model files,
  - isolated local environments,
  - localhost-only servers,
  - path containment for every generated file,
  - size caps and cleanup for generated depth/NPZ/point/video artifacts,
  - blocked diagnostics instead of placeholder geometry when dependencies are missing.

## Tests

- Geometry bundle schema validation.
- Path containment for bundle sidecars and generated outputs.
- Artifact labeling and sorting for learned/predicted geometry.
- Incomplete bundle rejection.
- API/frontend type handling for new bundle metadata.
- Existing backend/pipeline tests and frontend build.

## Assumptions

- This is a readiness milestone, not a commitment to ship LingBot-Map as the default reconstruction engine.
- Real Gaussian Splatting remains a first-class RoomSplat direction.
- Learned geometry outputs must be labeled honestly as predicted geometry unless downstream processing turns them into another verified artifact type.
- Future LingBot-Map/VGGT-style adapters stay optional and local-only.
