# Recognizable Splat Continuation

Goal: produce a local RoomSplat Gaussian splat that is recognizable in the browser viewer.

## Work completed

- Added robust point bounds for point/splat fallback camera fitting.
- Added a `Focus` control that targets a dense local point cluster for point-based artifacts.
- Added a Gaussian PLY fallback path that uses Nerfstudio `f_dc_*`, `opacity`, and `scale_*` properties when GaussianSplats3D times out.
- Restored the GaussianSplats3D loader timeout to 15 seconds so unsupported/slow PLYs fall back promptly.
- Ran and inspected existing local splats:
  - Objectron chair, 60 frames, 1000 iterations, 44,601 splat vertices, 10.6 MB.
  - Objectron cup, 53 frames, 1000 iterations, 12,412 splat vertices, 2.9 MB.
- Ran a new bounded Objectron shoe splat:
  - Project `daae7b0411d54bbba2b95f71341ad5df`.
  - 10 frames, Splatfacto, 1000 iterations, 12,255 splat vertices, 3.0 MB.
  - 10 frames, Splatfacto, 3000 iterations, 165,962 splat vertices, 41.2 MB.

## Browser verification

- The browser viewer loads the Nerfstudio PLYs as `splat_ply`.
- GaussianSplats3D still times out on the Nerfstudio PLYs.
- The new fallback displays Nerfstudio Gaussian PLYs as scaled alpha sprites instead of uniform point-cloud dots.
- Manual verification screenshots were saved under ignored `data/manual-verification/`.

Best current candidate:

- `data/manual-verification/recognizable-splat-chair-masked-1000-gaussian-fallback-large-view.png`

Assessment:

- Masked chair 1000 is visually recognizable as the orange bowl chair from the source Objectron frames.
- The masked chair project uses existing frame data from the local Objectron chair video, downscaled to 720x960 and background-damped outside the orange chair silhouette.
- Masked chair 1000 produced a real Nerfstudio `reconstruction/splat.ply`: 60 frames, 1000 Splatfacto iterations, 29,185 splat vertices, 7,239,472 bytes, 173.71 seconds.
- Browser screenshot pixel check for `recognizable-splat-chair-masked-1000-gaussian-fallback-large-view.png`: 598x830, 31,085 unique colors, 53,132 non-background pixels, 5,690 orange pixels, orange bbox 230x212 px.
- GaussianSplats3D native rendering still timed out and the viewer used the Gaussian PLY fallback.
- Shoe 3000 is visually stronger than cup/chair 1000 and shows a rough shoe/sole-like region, but it is still noisier than the masked chair result.
- Cup 1000 is not recognizable.
- Chair 1000 is only partially suggestive and not robustly recognizable.

## Validation run

- Frontend helper tests passed: 11 tests.
- Frontend Vite build passed with the existing chunk-size warning.

## Remaining risks / next step

- Goal can be completed after full backend/pipeline validation and commit/push.
- Remaining quality limitation: native GaussianSplats3D rendering still times out on Nerfstudio PLYs, so the browser screenshot uses the local Gaussian PLY fallback.
- Future quality work should make object masking/cropping a documented pipeline feature instead of an ad hoc local prep step.
