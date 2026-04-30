# Capture Guide

Good reconstruction starts with boring, consistent video. The v1 workflow uses imported video first, then stream capture later.

## Practical guidance

- Move slowly through the room.
- Keep objects in view from multiple angles.
- Avoid fast pans, motion blur, and abrupt exposure changes.
- Prefer bright, even lighting.
- Avoid reflective, transparent, and textureless surfaces when testing.
- Walk a loop when possible so camera pose estimation has overlap.
- Capture small rooms and short clips first while the pipeline is still being proven.

## Known limitations

- Gaussian splats can look visually useful without being metric-accurate.
- A `.ply` file may be either conventional point cloud data or splat data depending on the pipeline stage.
- `.glb` export depends on whether the selected reconstruction path can produce or convert to a mesh/scene representation.
