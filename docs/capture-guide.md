# Capture Guide

Good reconstruction starts with boring, consistent video. The v1 workflow uses imported video first, then stream capture later.

## Practical guidance

- Start with 10-30 second clips while the pipeline is still being proven.
- Prefer 1080p or better when storage allows; stable focus and low blur matter more than maximum resolution.
- High frame rate helps if motion is smooth, but avoid racing through the scene.
- Move slowly through the room.
- Keep objects in view from multiple angles.
- Avoid fast pans, motion blur, and abrupt exposure changes.
- Prefer bright, even lighting.
- Avoid reflective, transparent, and textureless surfaces when testing.
- Walk a loop when possible so camera pose estimation has overlap.
- Capture small rooms and short clips first while the pipeline is still being proven.
- For a first success case, film one textured object or one small room corner from a slow half-loop.

## Known limitations

- Gaussian splats can look visually useful without being metric-accurate.
- A `.ply` file may be either conventional point cloud data or splat data depending on the pipeline stage.
- `.glb` export depends on whether the selected reconstruction path can produce or convert to a mesh/scene representation.
- Browser preview is bounded for responsiveness; download large artifacts for full inspection.
