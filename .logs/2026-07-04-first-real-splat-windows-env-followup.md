# First Real Splat Windows Env Follow-up

Date: 2026-07-04

Goal: continue toward the first real local RoomSplat `reconstruction/splat.ply` and verify it in the browser viewer.

Completed:

- Installed local micromamba 2.8.1 under ignored `data/tools/micromamba`.
- Created isolated Nerfstudio candidate envs under ignored `data/tools/micromamba-root/envs/`.
- Added `ROOMSPLAT_NERFSTUDIO_PYTHON_PATH` support so readiness can check torch, nerfstudio, and gsplat inside the actual Nerfstudio environment instead of the backend Python.
- Hardened `NerfstudioSplatRunner` subprocess setup:
  - prepends env, env `bin`, `Scripts`, `Library/bin`, and configured FFmpeg/COLMAP directories to PATH,
  - sets UTF-8 subprocess IO to avoid Windows CP1252 crashes from Rich/Nerfstudio output,
  - infers Visual Studio Build Tools `PATH`, `INCLUDE`, and `LIB`,
  - supports NVIDIA env CUDA layout and conda-forge `Library/bin/nvcc.exe` layout,
  - passes `--no-gpu` to `ns-process-data images`,
  - passes configured `--colmap-cmd`.
- Downloaded official COLMAP 3.9.1 no-CUDA under ignored `data/tools` for Nerfstudio process-data compatibility.
- Verified app flow reaches:
  - frame copying,
  - COLMAP process-data,
  - Nerfstudio dataset generation,
  - `ns-train splatfacto`.

Environment attempts:

- `roomsplat-nerfstudio-py310`
  - Python 3.10, PyTorch 2.1.2+cu118, CUDA 11.8, Nerfstudio 1.1.5, gsplat 1.4.0.
  - Fails inside gsplat CUDA extension build with current VS 2022/CUDA 11.8 compatibility issues.
- `roomsplat-nerfstudio-cu124`
  - Python 3.10, PyTorch 2.6.0+cu124, Nerfstudio 1.1.5, gsplat 1.4.0.
  - Micromamba selected conda-forge CUDA 13.3 compiler packages. Driver supports CUDA UMD 13.3.
  - Fails/times out inside gsplat CUDA extension build. Latest clear failure is CCCL/MSVC traditional preprocessor handling; a 1-iteration smoke run timed out after 15 minutes and produced no splat.

Current result:

- No real `data/9522ce63dbfc454fb638fae38375863c/reconstruction/splat.ply` was produced.
- `metadata/splat_reconstruction.json` records `status: failed`, `is_reconstruction: false`, `output_path: null`.
- This is now a gsplat Windows CUDA build-matrix blocker, not a RoomSplat artifact/job routing blocker.

Validation:

- Focused tests passed repeatedly:
  - `$env:PYTHONPATH='backend'; py -3.12 -m pytest pipeline/tests/test_nerfstudio_splat_runner.py backend/tests/test_config.py`
  - Latest focused run: 12 passed.
- Full Python validation passed after docs/runner cleanup:
  - `$env:PYTHONPATH='backend'; py -3.12 -m pytest backend/tests pipeline/tests`
  - Result: 84 passed.
- Frontend validation passed with the bundled Node fallback because `npm` is not available on PATH in this PowerShell session:
  - `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe node_modules\vite\bin\vite.js build`
  - Result: passed with the existing Vite large chunk warning.
  - `C:\Users\ckajs\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe --experimental-strip-types --test frontend\tests\*.test.ts`
  - Result: 6 passed.

Remaining risk:

- The local ignored envs are large and experimental.
- The current app changes improve diagnostics and subprocess setup but do not complete the first real splat goal.
- Next best path is to pin a known-good gsplat Windows build matrix: either older MSVC tooling compatible with CUDA 11.8, or a newer Nerfstudio/gsplat/PyTorch/CUDA stack with a confirmed Windows extension build.
