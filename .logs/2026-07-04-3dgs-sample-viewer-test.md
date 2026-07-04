# 2026-07-04 3DGS sample viewer test

## Scope

- Tested the browser Three.js viewer against local sample data from `C:\project\3DGS_PLY_sample_data`.
- Kept sample artifacts and screenshots under ignored `data/` folders.
- No product direction change: this is still splat-first, with point-cloud fallback for inspection.

## Sample data

- Readme declares the cactus sample data as CC0 and requests credit URL `https://www.steam-studio.jp`.
- Postshot uncompressed PLY has ordinary `x/y/z` positions plus Gaussian-style attributes: `f_dc_0..2`, SH rest coefficients, opacity, scale, and rotation.
- SuperSplat compressed PLY uses packed chunk/sh fields and has no ordinary vertex positions.
- RealityCapture OBJ mesh exports exist in the sample folder, but the current viewer does not load OBJ directly.

## Local ignored test project

- Project id: `023ad4c91b794a0bbe6ec20f202596d7`.
- `reconstruction/cactus-splat.ply`: Postshot uncompressed sample, 31.4 MB, 139,410 points/splats.
- `reconstruction/cactus-supersplat-compressed.ply`: SuperSplat compressed sample, 8.1 MB.

## Findings

- GaussianSplats3D timed out on the Postshot sample in the current integration.
- The fallback PLY point renderer can display the Postshot sample as a recognizable cactus-like object when mapping `f_dc_0..2` to approximate RGB.
- The SuperSplat compressed sample cannot be displayed by the point fallback because it has no vertex `x/y/z` positions.
- The compressed sample now reports both causes clearly: splat timeout and point fallback failure.

## Changes

- Added a 15 second timeout around `DropInViewer.addSplatScene`.
- Disposed the splat object on loader failure.
- Enabled progressive loading for the splat attempt.
- Added PLYLoader custom mapping for `f_dc_0..2` and converted those coefficients to approximate display colors.
- Preserved combined error details when both splat load and point fallback fail.

## Validation

- Backend/pipeline test suite passed: 79 tests.
- Frontend helper tests passed: 5 tests.
- Frontend build passed with the usual chunk-size warning.
- Browser smoke passed for the Postshot fallback path.
- Browser smoke produced a clear unsupported-format message for the SuperSplat compressed path.
- Screenshot saved to ignored `data/manual-verification/sample-cactus-postshot-fallback-large-view.png`.
- Pixel check on the screenshot crop found 22,903 unique colors, so the viewer output is not blank.
- `git diff --check` passed with line-ending warnings only.

## Remaining work

- Add true support for Postshot/SuperSplat variants through a compatible splat renderer path or conversion step.
- Consider an OBJ-to-GLB import/conversion path if the RealityCapture mesh samples become useful for viewer tests.
