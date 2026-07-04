# Validation

Use the milestone-specific commands in `PLAN.md` as the source of truth.

## Current baseline

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

Optional frontend helper check in the bundled Node runtime:

```bash
node --experimental-strip-types --test frontend/tests/*.test.ts
```

## Expected smoke path

1. Create a local project.
2. Import a tiny video.
3. Create a frame extraction job.
4. Poll until job status is `succeeded` or `failed`.
5. Verify `metadata/video_import.json`, `metadata/frame_extraction.json`, `metadata/jobs/<job-id>.json`, `metadata/jobs/<job-id>.log`, and `frames/frame_*.png`.
6. Create a reconstruction-spike job.
7. Verify `metadata/reconstruction_spike.json` records dependency readiness and output contracts.
8. Create a debug-frame-cloud job with custom params such as `max_points`, `frame_step`, `arc_degrees`, and `plane_width`.
9. Verify `reconstruction/debug-frame-room.ply` and `metadata/debug_frame_cloud.json` exist and are marked debug/not reconstruction.
10. Verify `metadata/debug_frame_cloud.json` records params, sampled point count, source frame count, selected frame count, and `frame_planes[]`.
11. List artifacts through `GET /projects/{project_id}/artifacts`.
12. Load supported artifacts in the viewer or show explicit debug/unsupported states.
13. Verify the Three.js canvas is nonblank for `debug_frame_cloud_ply` and that debug report artifact switching still works.
14. Verify large-view mode, camera presets, grid/axes toggles, point size, color mode, frame markers, screenshot capture, and not-reconstruction warning.
15. Create exports through `POST /projects/{project_id}/exports`.
16. Verify `metadata/exports/<export-id>.json` records source artifact, format, generated time, artifact label, and `real`/`placeholder` status.
17. Download the exported file through the artifact download URL.
18. Confirm the backend is bound to `127.0.0.1` for local v1 use.
19. Confirm generated data remains ignored by Git.

## Validation principle

The app must not present placeholder reconstruction output as real reconstruction. Missing external reconstruction dependencies should produce clear, actionable messages.

## Real Reconstruction Preview v1

Focused validation for the COLMAP-backed point-cloud preview:

```bash
python -m pytest backend/tests/test_jobs.py backend/tests/test_artifacts.py pipeline/tests/test_colmap_sparse_runner.py
node --experimental-strip-types --test frontend/tests/*.test.ts
npm --prefix frontend run build
```

Manual/browser checks:

- Verify `reconstruct_point_cloud` fails with a clear COLMAP setup message when `colmap.exe` is not available.
- When COLMAP is installed, use a project with extracted frames and run `reconstruct_point_cloud`.
- Confirm `reconstruction/sparse-point-cloud.ply` is listed as `point_cloud_ply`.
- Confirm `metadata/reconstruction.json` reports `mode: reconstruction`, `is_reconstruction: true`, registered frame count, sparse point count, and quality status.
- Confirm debug frame planes still show an explicit not-reconstruction warning.
- Confirm the Three.js canvas is nonblank, fit/reset/orbit/zoom/point-size/color controls work, and artifact switching keeps debug and real outputs distinct.

Security baseline checks should cover path containment for project IDs, uploads, frame extraction sources, job paths, artifact IDs, artifact listing/downloads, and export outputs.

## Reconstruction Quality + Camera Path v1

Focused validation for the camera/path metadata and viewer overlays:

```bash
python -m pytest pipeline/tests/test_colmap_sparse_runner.py backend/tests/test_jobs.py backend/tests/test_artifacts.py
node --experimental-strip-types --test frontend/tests/*.test.ts
npm --prefix frontend run build
```

Objectron local sample results with COLMAP 4.1.0 no-CUDA, `preset=balanced`, `matcher=exhaustive`, `use_gpu=false`:

| Sample | Project | Extracted frames | Extraction stride | Registered frames | Sparse/PLY points | Cameras | Quality |
|---|---|---:|---:|---:|---:|---:|---|
| Objectron cup | `9522ce63dbfc454fb638fae38375863c` | 8 | 15 | 8 | 729 | 8 | inspectable |
| Objectron chair | `eef6d5739f524dc8a45eadc43aa0c5ec` | 14 | 18 | 14 | 3,723 | 14 | inspectable |
| Objectron shoe | `daae7b0411d54bbba2b95f71341ad5df` | 10 | 18 | 10 | 2,041 | 10 | inspectable |

Manual/browser checks:

- Confirm the selected `sparse-point-cloud.ply` loads as `point_cloud_ply`.
- Confirm stats show point count, cameras, path points, input frames, registered frames, and sparse points.
- Toggle points, cameras, path, grid, and axes independently.
- Confirm camera frustums and trajectory remain distinct from debug frame-plane markers.
- Confirm artifact ordering keeps `reconstruction/sparse-point-cloud.ply` above debug frame planes and placeholder exports.

## Real Splat Pipeline Exploration + First Local Splat Adapter v1

Focused validation for the Nerfstudio/Splatfacto adapter:

```bash
python -m pytest pipeline/tests/test_nerfstudio_splat_runner.py backend/tests/test_jobs.py backend/tests/test_artifacts.py
node --experimental-strip-types --test frontend/tests/*.test.ts
npm --prefix frontend run build
```

Local readiness on July 4, 2026:

- GPU: NVIDIA GeForce RTX 3080 Ti visible through `nvidia-smi`.
- CUDA driver runtime: visible through NVIDIA driver; `nvcc` was not on PATH.
- Backend Python: 3.12.13.
- Missing from backend Python runtime: `torch`, `nerfstudio`, `gsplat`, `pycolmap`, `open3d`.
- Missing from PATH: `ns-process-data`, `ns-train`, `ns-export`.
- COLMAP is not on PATH, but local ignored COLMAP 4.1.0 no-CUDA exists under `data/tools/`.

Objectron splat readiness checks with `method=splatfacto`, `max_iterations=3000`:

| Sample | Project | Input frames | Status | Output |
|---|---|---:|---|---|
| Objectron cup | `9522ce63dbfc454fb638fae38375863c` | 8 | blocked_missing_dependencies | no `splat.ply` |
| Objectron chair | `eef6d5739f524dc8a45eadc43aa0c5ec` | 14 | blocked_missing_dependencies | no `splat.ply` |
| Objectron shoe | `daae7b0411d54bbba2b95f71341ad5df` | 10 | blocked_missing_dependencies | no `splat.ply` |

Manual/browser checks:

- Start a `reconstruct_splat` job.
- Confirm missing Nerfstudio dependencies produce a succeeded readiness job with `metadata/splat_reconstruction.json`.
- Confirm no placeholder `reconstruction/splat.ply` is created when readiness is blocked.
- When Nerfstudio is installed, confirm `reconstruction/splat.ply` is listed as `splat_ply` and sorted above sparse point clouds.
