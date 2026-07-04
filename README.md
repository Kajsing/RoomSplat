# local-3d-room-mapper

Local Windows-first web app for video-to-3D reconstruction using a Gaussian Splatting / NeRF-style pipeline.

The first version focuses on the local engine: import a video, extract frames, run or spike a local reconstruction path, inspect the result, and export `.ply` / `.glb` artifacts.

Security model: v1 is a local single-user app. Bind the backend to `127.0.0.1`; do not expose it to an untrusted LAN or the public internet because there is no authentication yet.

## What works now

- FastAPI backend with `GET /health`.
- Local project storage with `GET /projects` and `POST /projects`.
- Video upload into project `input/` folders.
- Deterministic frame extraction into project `frames/` folders.
- Local background jobs for frame extraction, reconstruction-spike orchestration, debug frame planes, real sparse point-cloud reconstruction, and Nerfstudio-backed splat reconstruction readiness/training/export.
- Artifact discovery/download APIs with explicit labels for debug frame clouds, point clouds, real splats, GLB, and debug reports.
- Browser Three.js viewer with orbit/inspect controls, large-view mode, camera presets, orientation presets, stats, screenshot capture, frame markers for debug frame clouds, camera/path overlays for COLMAP point clouds, point cloud PLY, real `splat_ply` fallback viewing, and GLB scenes.
- Export APIs and UI controls for `.ply` / `.glb` outputs, including explicit placeholder labels for debug exports.
- Vite + React frontend displaying backend health, create/list projects, video upload, job status, and artifact viewer states.
- Focused security baseline docs and tests for path containment, upload limits, artifact downloads, and local-only assumptions.

## What it does not do yet

- Real Gaussian Splatting training is wired through a local Nerfstudio/Splatfacto adapter and has produced the first local Objectron cup `reconstruction/splat.ply` when using a compatible isolated Nerfstudio environment.
- Placeholder exports can be created from the reconstruction spike report for UI/workflow testing, but they are labeled as placeholders and are not real reconstruction.
- If Nerfstudio is missing, the splat job writes `metadata/splat_reconstruction.json` with actionable blockers and does not create fake splat output.
- The browser currently displays the first RoomSplat splat PLY through point-cloud fallback because GaussianSplats3D times out on the Nerfstudio PLY; this is a viewer-loader compatibility issue, not a fake-output path.
- Real sparse point-cloud reconstruction requires local COLMAP.
- General MP4/MOV extraction requires `ffmpeg` on PATH or `ROOMSPLAT_FFMPEG_PATH`.
- No live phone/webcam streaming yet.
- No native Android app.
- No cloud processing or user accounts.
- No construction-grade measurement guarantees.

## Windows prerequisites

- Python 3.12 recommended. On some Windows installs, use `py -3.12` if the `python` alias points to the Microsoft Store stub.
- Node.js 20+ and npm.
- Git.
- Optional for MP4/MOV/AVI/MKV/WebM extraction: ffmpeg on `PATH` or configured with `ROOMSPLAT_FFMPEG_PATH`.
- Optional for real sparse point-cloud reconstruction: COLMAP on `PATH` or configured with `ROOMSPLAT_COLMAP_PATH`.
- Optional for real Gaussian Splatting reconstruction: a separate conda-based Nerfstudio/Splatfacto environment with `ns-process-data`, `ns-train`, `ns-export`, PyTorch/CUDA, CUDA toolkit, and Visual Studio C++ Build Tools.

GIF fixtures and tests work without ffmpeg. Real splat training is wired through the adapter and can reach local Nerfstudio/COLMAP on this machine.

Current local machine note from the July 4, 2026 preflight: RTX 3080 Ti, Visual Studio Build Tools, FFmpeg, COLMAP 3.9.1 no-CUDA, micromamba-based Nerfstudio, PyTorch 2.1.2+cu118, `nvcc`, Nerfstudio 1.1.5, and precompiled `gsplat==1.4.0+pt21cu118` are present/configured locally. The Objectron cup `reconstruct_splat` path produces a real `reconstruction/splat.ply` with `status: succeeded`.

## Configure

Copy `.env.example` to `.env` if you want local overrides. The backend reads `.env` from the repo root; process environment variables still take precedence. Important defaults:

- `ROOMSPLAT_DATA_DIR=./data`
- `ROOMSPLAT_MAX_UPLOAD_MB=2048`
- `ROOMSPLAT_FFMPEG_TIMEOUT_SECONDS=1800`
- `ROOMSPLAT_COLMAP_PATH=` optional full path to `colmap.exe` or `COLMAP.bat`
- `ROOMSPLAT_NERFSTUDIO_BIN_DIR=` optional path to the Nerfstudio environment `Scripts`/`bin` folder
- `ROOMSPLAT_NERFSTUDIO_PYTHON_PATH=` optional path to that environment's `python.exe` for environment-specific readiness checks
- `ROOMSPLAT_NS_PROCESS_DATA_PATH=`, `ROOMSPLAT_NS_TRAIN_PATH`, `ROOMSPLAT_NS_EXPORT_PATH` optional per-command overrides
- `VITE_ROOMSPLAT_API_URL=http://127.0.0.1:8000`

Keep generated project data under `data/` or another ignored local folder.

## Install backend

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Start backend

```bash
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

## Install frontend

```bash
npm --prefix frontend install
```

## Start frontend

```bash
npm --prefix frontend run dev
```

Open the Vite URL shown in the terminal, usually `http://127.0.0.1:5173`.

## Workflow

1. Create a project.
2. Upload a short video or GIF.
3. Extract frames through the local job flow.
4. Create debug frame planes if you want a quick flat-frame-in-3D artifact for testing viewer orientation and controls. Optional parameters are `max_points`, `frame_step`, `arc_degrees`, and `plane_width`.
5. Run point cloud reconstruction to create a real COLMAP sparse point cloud at `reconstruction/sparse-point-cloud.ply`. Choose quick/balanced/detail presets as guidance for the extraction density you want to compare.
6. Run splat reconstruction to attempt Nerfstudio/Splatfacto. If dependencies are missing, inspect the generated readiness diagnosis; if dependencies are ready, the job writes `reconstruction/splat.ply`.
7. Run the reconstruction spike if you want the older multi-adapter dependency report.
8. Inspect listed artifacts/debug reports in the browser viewer.
9. Export `.ply` or `.glb` artifacts when available.

Placeholder exports are allowed only for workflow/debug testing and are labeled as placeholders.
Debug frame plane artifacts are also debug-only and must not be described as reconstruction output.

If COLMAP is not installed, the point-cloud reconstruction job fails with setup guidance instead of writing fake output.
If Nerfstudio is not installed, the splat reconstruction job succeeds as a readiness check, writes `metadata/splat_reconstruction.json`, and does not write `reconstruction/splat.ply`. If Nerfstudio is installed but training/export fails, the same metadata file records the failed command output and still avoids fake splat output.

## Nerfstudio setup target

The real-splat setup target is a Windows-native isolated Nerfstudio environment, not Docker or cloud upload. Use a tested Python/PyTorch/CUDA/gsplat/MSVC combination, install CUDA Toolkit so `nvcc` is available, install Visual Studio C++ Build Tools, then install Nerfstudio and verify:

```bash
ns-process-data --help
ns-train splatfacto --help
ns-export gaussian-splat --help
```

After that, set `ROOMSPLAT_NERFSTUDIO_BIN_DIR` to the environment `Scripts` folder or set the three individual `ROOMSPLAT_NS_*_PATH` values, then rerun the `reconstruct_splat` job.

Local July 4, 2026 experiments used ignored micromamba environments under `data/tools/micromamba-root/envs/`. Python 3.8 hit modern dependency resolver issues. The first successful local stack is Python 3.10, PyTorch 2.1.2+cu118, Nerfstudio 1.1.5, and the precompiled Windows wheel `gsplat==1.4.0+pt21cu118` from `https://docs.gsplat.studio/whl/pt21cu118`. RoomSplat prepends the isolated environment paths, configured FFmpeg/COLMAP paths, UTF-8 subprocess settings, Visual Studio build paths, and both common `nvcc` layouts.

## Run tests

```bash
python -m pytest backend/tests pipeline/tests
npm --prefix frontend run build
```

If `python` opens the Windows Store alias, use:

```bash
py -3.12 -m pytest backend/tests pipeline/tests
```

If npm is not available in your shell but Node is, use the direct Vite CLI from `frontend/` as a fallback:

```bash
node node_modules/vite/bin/vite.js build
```

## Generated data

Generated videos, frames, reconstruction outputs, splats, checkpoints, and exports belong under `data/` or per-project output folders and must not be committed.

## Capture and output notes

- Start with short, slow clips of a small room or object.
- Prefer bright, even lighting and overlapping camera paths.
- Avoid fast pans, reflective surfaces, transparent objects, and textureless walls while testing.
- `point_cloud_ply` is a conventional point cloud.
- `debug_frame_cloud_ply` is a deterministic viewer/debug point cloud sampled from flat extracted frames and placed in 3D; it is not a reconstruction.
- `reconstruction/sparse-point-cloud.ply` is a real COLMAP sparse `point_cloud_ply` artifact when point-cloud reconstruction succeeds.
- `splat_ply` is Gaussian splat data stored in a PLY-like format, not a conventional point cloud.
- `reconstruction/splat.ply` is considered real only when `metadata/splat_reconstruction.json` has `status: succeeded` and `is_reconstruction: true`.
- `mesh_glb` is a portable scene/mesh container only when a real conversion path exists.
- Large PLY files should be downloaded for full inspection; the debug frame planes generator caps output at 50,000 points.
- Debug frame plane metadata records sampled frame planes, point counts, params, and `not_reconstruction: true`.
- Real sparse reconstruction metadata is written to `metadata/reconstruction.json` with COLMAP workspace, input frame count, registered frame count, point count, camera intrinsics, registered image poses, camera centers, camera path, trajectory bounds, params, and quality notes.
- The viewer can show/hide points, COLMAP camera frustums, camera path, grid, and axes independently for real point-cloud artifacts.
- The viewer orientation control can leave source axes unchanged, flip X/Y/Z, or convert between Z-up and Y-up for imported PLY/GLB/splat artifacts that appear upside down or on the wrong axis.
- The quick/balanced/detail reconstruction presets are recorded with the run and currently provide extraction-density guidance; they do not silently re-extract frames for an existing project.

## Documentation map

- `SPEC.yaml` - product and technical requirements.
- `PLAN.md` - milestone order, acceptance criteria, and validation commands.
- `IMPLEMENT.md` - implementation runbook.
- `ARCHITECTURE.md` - system boundaries and data flow.
- `DOCUMENTATION.md` - current status, decisions, known issues, and commands run.
- `docs/capture-guide.md` - video capture tips.
- `docs/project-format.md` - project storage, artifact labels, and export metadata.
- `docs/security-baseline.md` - Milestone 8 focused security baseline.
- `docs/risks.md` - current technical risks and mitigations.
- `docs/archive/roomsplat-dev-doc.md` - original handoff specification kept as historical reference.
