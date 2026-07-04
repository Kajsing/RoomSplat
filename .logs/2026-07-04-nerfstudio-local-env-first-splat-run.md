# Nerfstudio local environment + first splat run attempt

Date: 2026-07-04

## Goal

Configure and verify the Windows-native Nerfstudio/Splatfacto path for RoomSplat, then run `reconstruct_splat` on the Objectron cup project.

## Local preflight

- Repo was clean on `Main` before changes.
- Python launcher: `py -3.12` is available.
- Plain `python` resolves to the Windows Store alias in this shell and is not usable for validation.
- GPU: `nvidia-smi` reports NVIDIA GeForce RTX 3080 Ti.
- FFmpeg: available through WinGet.
- COLMAP: available locally at `data/tools/colmap-4.1.0-nocuda/bin/colmap.exe`.
- Visual Studio Build Tools 2022: installed under `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools`.
- `cl.exe`: available after calling `VC\Auxiliary\Build\vcvars64.bat`.
- CUDA Toolkit/`nvcc`: not found.
- Nerfstudio CLIs: `ns-process-data`, `ns-train`, and `ns-export` not found.

## Changes

- Added dependency-free `.env` reading to `backend/app/config.py`.
- Created local ignored `.env` with known data, FFmpeg, and COLMAP paths.
- Extended `NerfstudioSplatRunner.assess()` with supporting dependency diagnostics for `nvidia-smi`, `nvcc`, `cl`, `ffmpeg`, and `colmap`.
- Passed configured FFmpeg/COLMAP paths into the splat reconstruction service from the worker.
- Added focused tests for `.env` loading and supporting tool path diagnostics.
- Updated README, `.env.example`, pipeline docs, and `DOCUMENTATION.md`.

## Objectron cup run

Project: `9522ce63dbfc454fb638fae38375863c`

Command path: direct backend service call using `.env` config.

Result:

- `metadata/splat_reconstruction.json` updated.
- `status: blocked_missing_dependencies`.
- `output_path: null`.
- No fake `reconstruction/splat.ply` written.
- Blockers are the missing Nerfstudio CLIs: `ns-process-data`, `ns-train`, `ns-export`.
- Supporting readiness now correctly shows GPU, Visual Studio compiler, FFmpeg, and COLMAP status.

## Recommended next setup step

Install CUDA Toolkit so `nvcc` is available, create an isolated Windows-native Nerfstudio environment with compatible PyTorch/CUDA and Nerfstudio, run install/build commands from a Visual Studio Developer Command Prompt, then set `ROOMSPLAT_NERFSTUDIO_BIN_DIR` or the three `ROOMSPLAT_NS_*_PATH` values and rerun `reconstruct_splat`.

## Validation

- `py -3.12 -m pytest backend/tests/test_config.py pipeline/tests/test_nerfstudio_splat_runner.py backend/tests/test_jobs.py -q`
- Result: passed, 32 tests.
- `py -3.12 -m pytest backend/tests pipeline/tests`
- Result: passed, 79 tests.
- `npm --prefix frontend run build`
- Result: not run because `npm` is not available on PATH in this shell.
- Bundled Node fallback: `node node_modules/vite/bin/vite.js build` from `frontend/`
- Result: passed. Vite reported the existing large chunk warning for viewer dependencies.
- `git diff --check`
- Result: passed with Git line-ending warnings only.
