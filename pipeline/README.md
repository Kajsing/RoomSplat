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

Current adapters:

- `colmap`: camera poses and sparse conventional point cloud.
- `nerfstudio-splatfacto`: interim full splat-training path.
- `gsplat`: lower-level future custom/fast/generative splat boundary.
- `open3d-debug`: optional point-cloud inspection tooling.

## Nerfstudio splat adapter

The first real splat adapter is `reconstruct_splat`, backed by Nerfstudio/Splatfacto.

The backend job:

- reads existing extracted frames from `metadata/frame_extraction.json`,
- checks `ns-process-data`, `ns-train`, `ns-export`, Python-side import visibility, GPU/CUDA signals, Visual Studio C++ compiler readiness, FFmpeg, and COLMAP,
- writes `metadata/splat_reconstruction.json` for both blocked and successful runs,
- runs `ns-process-data images`, `ns-train splatfacto`, and `ns-export gaussian-splat` when dependencies are ready,
- copies the exported Gaussian splat PLY to `reconstruction/splat.ply`,
- never writes fake splat geometry when dependencies are missing.

Configuration options:

- `ROOMSPLAT_NERFSTUDIO_BIN_DIR`
- `ROOMSPLAT_NS_PROCESS_DATA_PATH`
- `ROOMSPLAT_NS_TRAIN_PATH`
- `ROOMSPLAT_NS_EXPORT_PATH`

The recommended Windows path is an isolated Nerfstudio environment rather than adding Nerfstudio to the backend venv. Keep generated Nerfstudio datasets, checkpoints, configs, exports, and splats inside the ignored project data directory.

Current local preflight from July 4, 2026:

- GPU driver and `nvidia-smi` are available for an RTX 3080 Ti.
- Visual Studio Build Tools 2022 are installed; run install/training commands from a Developer Command Prompt or call `vcvars64.bat` before building CUDA extensions.
- FFmpeg is available and local COLMAP is configured under `data/tools`.
- CUDA Toolkit/`nvcc` is not installed or not on `PATH`.
- `ns-process-data`, `ns-train`, and `ns-export` are not installed or not on `PATH`.
- The Objectron cup `reconstruct_splat` run therefore writes blocked readiness metadata with `output_path: null` and no `reconstruction/splat.ply`.

Output labels must stay explicit:

- `camera_poses`: camera intrinsics/extrinsics.
- `point_cloud_ply`: conventional point cloud, not splats.
- `splat_ply`: Gaussian splat data.

Primary references:

- https://docs.nerf.studio/quickstart/installation.html
- https://docs.nerf.studio/nerfology/methods/splat.html
- https://colmap.github.io/pycolmap/index.html
- https://github.com/nerfstudio-project/gsplat/blob/main/docs/INSTALL_WIN.md
- https://www.open3d.org/docs/release/getting_started.html
