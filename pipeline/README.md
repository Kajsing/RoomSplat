# Pipeline

Milestone 3 supports deterministic frame extraction for tiny animated GIF fixtures without external binaries. This keeps tests small and reproducible on Windows.

General video formats such as `.mp4`, `.mov`, `.avi`, `.mkv`, and `.webm` are accepted by the app upload path. Extracting frames from those formats requires `ffmpeg` on `PATH` or `ROOMSPLAT_FFMPEG_PATH` / `FFMPEG_PATH` set to the executable path.

## Inspect a tiny fixture

```bash
python pipeline/scripts/inspect_video.py --video path/to/tiny.gif
```

## Extract frames

```bash
python pipeline/scripts/extract_frames.py --video path/to/tiny.gif --output data/tmp-frames --stride 2 --max-frames 10
```

Frames are written as `frame_000001.png`, `frame_000002.png`, and so on. Metadata is printed as JSON by the CLI and written under project `metadata/` by the backend API.

## Reconstruction spike

Milestone 4 is adapter-first. The app does not run reconstruction training unless local dependencies are present and explicitly wired through an adapter.

The selected interim path is:

```text
frames -> COLMAP/pycolmap poses -> Nerfstudio Splatfacto -> reconstruction/splat.ply
```

Run the spike against a project:

```bash
python pipeline/scripts/run_reconstruction_spike.py --project data/<project-id> --json --write-report
```

Run it against any frames directory:

```bash
python pipeline/scripts/run_reconstruction_spike.py --frames-dir data/<project-id>/frames
```

The script:

- validates that extracted frames exist,
- reports frame count and resolution,
- checks local availability of `colmap`, `pycolmap`, `ns-process-data`, `ns-train`, `nerfstudio`, `torch`, `gsplat`, and `open3d`,
- records expected artifact contracts,
- writes `metadata/reconstruction_spike.json` when `--project --write-report` is used,
- prints stop-condition guidance instead of producing fake reconstruction output.

## Adapter contract

Adapters expose dependency checks, readiness status, expected artifact contracts, and next setup steps.

Learned/feed-forward geometry adapters must use the shared geometry bundle contract from
`pipeline.adapters.base`:

- call `learned_geometry_expected_outputs()` when declaring the expected manifest and primary PLY;
- validate the declaration with `validate_geometry_expected_outputs()` in adapter tests;
- write the manifest to `metadata/geometry_bundle.json`;
- label the manifest as `learned_geometry_bundle`;
- label the primary predicted PLY as `predicted_point_cloud_ply`, not `point_cloud_ply` or `splat_ply`.

This contract is only a local artifact boundary. It does not add a learned-model runtime,
checkpoint loader, automatic download, or LingBot-Map dependency.

`pipeline.adapters.learned_geometry_import` provides the first concrete preflight helpers
for completed local learned-output folders:

- `inspect_learned_geometry_output(source_dir, primary_ply="points.ply")` validates a LingBot/BSS-inspired folder with `.complete.json`, primary PLY, optional `traj.txt`, optional `intrinsics.txt`, optional `sampling.json`, and declared frame sidecar folders.
- `learned_geometry_import_assessment()` declares the RoomSplat outputs a future adapter/import job should produce: `metadata/geometry_bundle.json` and `reconstruction/learned-point-cloud.ply`.
- `learned_geometry_expected_sidecars(frame_keys)` returns the sidecar paths implied by completion metadata.

These helpers are for preflight and normalization only. They do not import LingBot-Map,
load model checkpoints, run inference, download weights, or start an external viewer.

Current adapters:

- `colmap`: camera poses and sparse conventional point cloud.
- `nerfstudio-splatfacto`: interim full splat-training path.
- `gsplat`: lower-level future custom/fast/generative splat boundary.
- `open3d-debug`: optional point-cloud inspection tooling.

## Nerfstudio splat adapter

The first real splat adapter is `reconstruct_splat`, backed by Nerfstudio/Splatfacto.

The backend job:

- reads existing extracted frames from `metadata/frame_extraction.json`,
- checks `ns-process-data`, `ns-train`, `ns-export`, Python-side import visibility, backend Python runtime, conda availability, GPU/CUDA signals, Visual Studio C++ compiler readiness, FFmpeg, and COLMAP,
- writes `metadata/splat_reconstruction.json` for both blocked and successful runs,
- runs `ns-process-data images`, `ns-train splatfacto`, and `ns-export gaussian-splat` when dependencies are ready,
- passes `--viewer.quit-on-train-completion True` so short local smoke trainings return control after `--max-num-iterations`,
- copies the exported Gaussian splat PLY to `reconstruction/splat.ply`,
- never writes fake splat geometry when dependencies are missing.

Configuration options:

- `ROOMSPLAT_NERFSTUDIO_BIN_DIR`
- `ROOMSPLAT_NS_PROCESS_DATA_PATH`
- `ROOMSPLAT_NS_TRAIN_PATH`
- `ROOMSPLAT_NS_EXPORT_PATH`
- `ROOMSPLAT_NERFSTUDIO_PYTHON_PATH`

The recommended Windows path is an isolated micromamba/conda Nerfstudio environment rather than adding Nerfstudio to the backend venv. Keep generated Nerfstudio datasets, checkpoints, configs, exports, and splats inside the ignored project data directory.

Current local preflight from July 4, 2026:

- GPU driver and `nvidia-smi` are available for an RTX 3080 Ti.
- Visual Studio Build Tools 2022 are installed; the adapter now infers the MSVC `PATH`, `INCLUDE`, and `LIB` values for subprocesses.
- FFmpeg is available and local COLMAP is configured under `data/tools`.
- Backend Python is 3.12; the adapter reports this for diagnostics, but Nerfstudio should still be installed in its own isolated Python environment. Local Python 3.8 hit modern dependency resolver issues, so the current experiments use Python 3.10.
- Local micromamba is installed under ignored `data/tools/micromamba`.
- `roomsplat-nerfstudio-py310` can import PyTorch 2.1.2+cu118, Nerfstudio 1.1.5, and precompiled `gsplat==1.4.0+pt21cu118` from `https://docs.gsplat.studio/whl/pt21cu118`.
- `roomsplat-nerfstudio-cu124` can import PyTorch 2.6.0+cu124, Nerfstudio 1.1.5, and gsplat 1.4.0; its conda-forge CUDA compiler layout puts `nvcc.exe` under `Library/bin`.
- The adapter supports both `env/bin/nvcc.exe` and `env/Library/bin/nvcc.exe` layouts for `CUDA_HOME`.
- COLMAP 3.9.1 no-CUDA is currently used for Nerfstudio process-data compatibility. COLMAP 4.1.0 works for RoomSplat sparse point-cloud jobs, but Nerfstudio 1.1.5 still sends `SiftExtraction.use_gpu`, which COLMAP 4.1 no longer accepts.
- The Objectron cup `reconstruct_splat` run produces `reconstruction/splat.ply` with `status: succeeded` using the `py310` environment and precompiled gsplat wheel.
- Browser verification lists the artifact as `splat_ply` and displays it through point-cloud fallback with 788 vertices. GaussianSplats3D still times out on this Nerfstudio PLY, so native browser splat rendering remains a loader-compatibility task.

Output labels must stay explicit:

- `camera_poses`: camera intrinsics/extrinsics.
- `point_cloud_ply`: conventional point cloud, not splats.
- `splat_ply`: Gaussian splat data.
- `predicted_point_cloud_ply`: learned/predicted point cloud declared by a valid geometry bundle.
- `learned_geometry_bundle`: validated `metadata/geometry_bundle.json` metadata, not a 3D renderable artifact.

Primary references:

- https://docs.nerf.studio/quickstart/installation.html
- https://docs.nerf.studio/nerfology/methods/splat.html
- https://colmap.github.io/pycolmap/index.html
- https://github.com/nerfstudio-project/gsplat/blob/main/docs/INSTALL_WIN.md
- https://www.open3d.org/docs/release/getting_started.html
