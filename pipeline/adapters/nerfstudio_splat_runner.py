from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


class NerfstudioSplatRunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class NerfstudioSplatPaths:
    frames_dir: Path
    dataset_dir: Path
    output_dir: Path
    export_dir: Path
    final_splat_ply: Path


@dataclass(frozen=True)
class SplatDependency:
    name: str
    available: bool
    kind: str
    detail: str


@dataclass(frozen=True)
class SplatReadiness:
    status: str
    summary: str
    dependencies: tuple[SplatDependency, ...]
    blockers: tuple[str, ...]
    next_steps: tuple[str, ...]

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"


@dataclass(frozen=True)
class NerfstudioSplatRunResult:
    adapter: str
    method: str
    paths: NerfstudioSplatPaths
    process_command: list[str]
    train_command: list[str]
    export_command: list[str]
    config_path: Path
    exported_ply: Path
    command_count: int


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class NerfstudioSplatRunner:
    name = "nerfstudio-splatfacto"

    def __init__(
        self,
        *,
        ns_process_data_path: str | None = None,
        ns_train_path: str | None = None,
        ns_export_path: str | None = None,
        nerfstudio_bin_dir: str | None = None,
        nerfstudio_python_path: str | None = None,
        ffmpeg_path: str | None = None,
        colmap_path: str | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self.ns_process_data_path = ns_process_data_path
        self.ns_train_path = ns_train_path
        self.ns_export_path = ns_export_path
        self.nerfstudio_bin_dir = nerfstudio_bin_dir
        self.nerfstudio_python_path = nerfstudio_python_path
        self.ffmpeg_path = ffmpeg_path
        self.colmap_path = colmap_path
        self._command_runner = command_runner or self._run_subprocess

    def assess(self) -> SplatReadiness:
        dependencies = (
            _executable_dependency("ns-process-data", self.ns_process_data_path, self.nerfstudio_bin_dir),
            _executable_dependency("ns-train", self.ns_train_path, self.nerfstudio_bin_dir),
            _executable_dependency("ns-export", self.ns_export_path, self.nerfstudio_bin_dir),
            _python_module_dependency("torch"),
            _python_module_dependency("nerfstudio"),
            _python_module_dependency("gsplat"),
            _python_runtime_dependency(),
            _executable_dependency("conda", None, None, required=False),
            _nerfstudio_env_module_dependency("nerfstudio-env-torch", self.nerfstudio_python_path, "torch"),
            _nerfstudio_env_module_dependency("nerfstudio-env-nerfstudio", self.nerfstudio_python_path, "nerfstudio"),
            _nerfstudio_env_module_dependency("nerfstudio-env-gsplat", self.nerfstudio_python_path, "gsplat"),
            _nerfstudio_env_executable_dependency(
                "nerfstudio-env-nvcc",
                self.nerfstudio_python_path,
                self.nerfstudio_bin_dir,
                "nvcc",
            ),
            _executable_dependency("nvidia-smi", None, None, required=False),
            _executable_dependency("nvcc", None, None, required=False),
            _visual_studio_cl_dependency(),
            _executable_dependency("ffmpeg", self.ffmpeg_path, None, required=False),
            _executable_dependency("colmap", self.colmap_path, None, required=False),
        )
        required = dependencies[:3]
        blockers = tuple(dependency.detail for dependency in required if not dependency.available)
        if blockers:
            status = "blocked_missing_dependencies"
            summary = "Nerfstudio CLI dependencies are not ready, so no splat training was attempted."
        else:
            status = "ready"
            summary = "Nerfstudio CLI dependencies are available; splat training can be attempted."
        return SplatReadiness(
            status=status,
            summary=summary,
            dependencies=dependencies,
            blockers=blockers,
            next_steps=_next_steps(blockers),
        )

    def build_commands(
        self,
        paths: NerfstudioSplatPaths,
        *,
        method: str = "splatfacto",
        max_iterations: int | None = None,
    ) -> tuple[list[str], list[str], list[str]]:
        ns_process_data = _resolve_executable("ns-process-data", self.ns_process_data_path, self.nerfstudio_bin_dir)
        ns_train = _resolve_executable("ns-train", self.ns_train_path, self.nerfstudio_bin_dir)
        ns_export = _resolve_executable("ns-export", self.ns_export_path, self.nerfstudio_bin_dir)

        process_command = [
            ns_process_data,
            "images",
            "--data",
            str(paths.frames_dir),
            "--output-dir",
            str(paths.dataset_dir),
            "--no-gpu",
        ]
        if self.colmap_path:
            process_command.extend(["--colmap-cmd", str(Path(self.colmap_path).expanduser())])
        train_command = [
            ns_train,
            method,
            "--data",
            str(paths.dataset_dir),
            "--output-dir",
            str(paths.output_dir),
            "--viewer.quit-on-train-completion",
            "True",
        ]
        if max_iterations is not None:
            train_command.extend(["--max-num-iterations", str(max_iterations)])

        export_command = [
            ns_export,
            "gaussian-splat",
            "--load-config",
            "<config.yml>",
            "--output-dir",
            str(paths.export_dir),
        ]
        return process_command, train_command, export_command

    def run(
        self,
        paths: NerfstudioSplatPaths,
        *,
        method: str = "splatfacto",
        max_iterations: int | None = None,
    ) -> NerfstudioSplatRunResult:
        readiness = self.assess()
        if not readiness.is_ready:
            raise NerfstudioSplatRunnerError(readiness.summary)

        paths.dataset_dir.mkdir(parents=True, exist_ok=True)
        paths.output_dir.mkdir(parents=True, exist_ok=True)
        paths.export_dir.mkdir(parents=True, exist_ok=True)
        paths.final_splat_ply.parent.mkdir(parents=True, exist_ok=True)
        process_command, train_command, export_command_template = self.build_commands(
            paths,
            method=method,
            max_iterations=max_iterations,
        )

        self._run(process_command)
        self._run(train_command)
        config_path = find_latest_config(paths.output_dir)
        export_command = [
            str(config_path) if argument == "<config.yml>" else argument
            for argument in export_command_template
        ]
        self._run(export_command)
        exported_ply = find_exported_splat_ply(paths.export_dir)
        shutil.copyfile(exported_ply, paths.final_splat_ply)

        return NerfstudioSplatRunResult(
            adapter=self.name,
            method=method,
            paths=paths,
            process_command=process_command,
            train_command=train_command,
            export_command=export_command,
            config_path=config_path,
            exported_ply=exported_ply,
            command_count=3,
        )

    def _run(self, command: Sequence[str]) -> None:
        completed = self._command_runner(command)
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            detail = stderr or stdout or f"exit code {completed.returncode}"
            raise NerfstudioSplatRunnerError(f"Nerfstudio command failed: {Path(command[0]).name}: {detail}")

    def _run_subprocess(self, command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self._subprocess_env(),
        )

    def _subprocess_env(self) -> dict[str, str]:
        env = _visual_studio_build_env(os.environ.copy())
        prefix = _infer_nerfstudio_env_prefix(self.nerfstudio_python_path, self.nerfstudio_bin_dir)
        if not prefix:
            return env
        path_entries = [
            prefix,
            prefix / "bin",
            prefix / "Scripts",
            prefix / "Library" / "bin",
        ]
        path_entries.extend(_configured_tool_dirs(self.ffmpeg_path, self.colmap_path))
        existing_path = env.get("PATH", "")
        env["PATH"] = os.pathsep.join(str(path) for path in path_entries if path.exists())
        if existing_path:
            env["PATH"] = f"{env['PATH']}{os.pathsep}{existing_path}" if env["PATH"] else existing_path
        cuda_home = _infer_cuda_home(prefix)
        env.setdefault("CUDA_HOME", str(cuda_home))
        env.setdefault("CUDA_PATH", str(cuda_home))
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("DISTUTILS_USE_SDK", "1")
        env.setdefault(
            "NVCC_PREPEND_FLAGS",
            "-allow-unsupported-compiler -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -DCCCL_IGNORE_MSVC_TRADITIONAL_PREPROCESSOR_WARNING",
        )
        env.setdefault("CL", "/D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH /Zc:preprocessor")
        return env


def find_latest_config(output_dir: Path) -> Path:
    candidates = sorted(output_dir.rglob("config.yml"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        raise NerfstudioSplatRunnerError("Nerfstudio training finished without a config.yml file.")
    return candidates[0]


def find_exported_splat_ply(export_dir: Path) -> Path:
    preferred = export_dir / "splat.ply"
    if preferred.is_file():
        return preferred
    candidates = sorted(export_dir.glob("*.ply"))
    if not candidates:
        raise NerfstudioSplatRunnerError("Nerfstudio export finished without a Gaussian splat PLY.")
    return candidates[0]


def _resolve_executable(executable_name: str, configured_path: str | None, configured_dir: str | None) -> str:
    if configured_path:
        candidate = Path(configured_path).expanduser()
        if not candidate.is_file():
            raise NerfstudioSplatRunnerError(f"Configured {executable_name} executable was not found: {configured_path}")
        return str(candidate.resolve())
    if configured_dir:
        suffix = ".exe" if not executable_name.endswith(".exe") else ""
        candidate = Path(configured_dir).expanduser() / f"{executable_name}{suffix}"
        if not candidate.is_file():
            raise NerfstudioSplatRunnerError(f"Configured Nerfstudio bin dir does not contain {executable_name}: {configured_dir}")
        return str(candidate.resolve())
    discovered = shutil.which(executable_name) or shutil.which(f"{executable_name}.exe")
    if discovered:
        return discovered
    raise NerfstudioSplatRunnerError(f"{executable_name} was not found on PATH.")


def _infer_nerfstudio_env_prefix(python_path: str | None, configured_dir: str | None) -> Path | None:
    if python_path:
        python = Path(python_path).expanduser()
        if python.name.lower().startswith("python") and python.parent.name.lower() in {"scripts", "bin"}:
            return python.parent.parent
        return python.parent
    if configured_dir:
        configured = Path(configured_dir).expanduser()
        if configured.name.lower() in {"scripts", "bin"}:
            return configured.parent
    return None


def _resolve_env_executable(
    executable_name: str,
    python_path: str | None,
    configured_dir: str | None,
) -> Path | None:
    prefix = _infer_nerfstudio_env_prefix(python_path, configured_dir)
    if not prefix:
        return None
    suffix = ".exe" if not executable_name.endswith(".exe") else ""
    for directory in (prefix, prefix / "bin", prefix / "Scripts", prefix / "Library" / "bin"):
        candidate = directory / f"{executable_name}{suffix}"
        if candidate.is_file():
            return candidate.resolve()
    return None


def _infer_cuda_home(prefix: Path) -> Path:
    conda_forge_cuda = prefix / "Library"
    if (conda_forge_cuda / "bin" / "nvcc.exe").is_file():
        return conda_forge_cuda
    return prefix


def _configured_tool_dirs(*configured_paths: str | None) -> list[Path]:
    dirs: list[Path] = []
    for configured_path in configured_paths:
        if not configured_path:
            continue
        path = Path(configured_path).expanduser()
        directory = path.parent if path.suffix else path
        if directory not in dirs:
            dirs.append(directory)
    return dirs


def _executable_dependency(
    executable_name: str,
    configured_path: str | None,
    configured_dir: str | None,
    *,
    required: bool = True,
) -> SplatDependency:
    try:
        path = _resolve_executable(executable_name, configured_path, configured_dir)
        return SplatDependency(executable_name, True, "executable", path)
    except NerfstudioSplatRunnerError as exc:
        prefix = "Required" if required else "Optional"
        return SplatDependency(executable_name, False, "executable", f"{prefix}: {exc}")


def _nerfstudio_env_executable_dependency(
    name: str,
    python_path: str | None,
    configured_dir: str | None,
    executable_name: str,
) -> SplatDependency:
    path = _resolve_env_executable(executable_name, python_path, configured_dir)
    if path:
        return SplatDependency(name, True, "executable", str(path))
    return SplatDependency(
        name,
        False,
        "executable",
        f"Optional: {executable_name} was not found inside the configured Nerfstudio environment.",
    )


def _visual_studio_cl_dependency() -> SplatDependency:
    path = shutil.which("cl") or shutil.which("cl.exe")
    if path:
        return SplatDependency("cl", True, "executable", path)
    known_vcvars = (
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build/vcvars64.bat"),
    )
    for vcvars in known_vcvars:
        if vcvars.is_file():
            return SplatDependency(
                "cl",
                True,
                "executable",
                f"Visual Studio C++ toolchain found via {vcvars}; run commands from a Developer Command Prompt or call vcvars64.bat first.",
            )
    return SplatDependency(
        "cl",
        False,
        "executable",
        "Optional: cl.exe was not found on PATH and no known Visual Studio vcvars64.bat was found.",
    )


@lru_cache(maxsize=1)
def _known_vcvars64_path() -> Path | None:
    known_vcvars = (
        Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvars64.bat"),
        Path("C:/Program Files/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build/vcvars64.bat"),
    )
    for vcvars in known_vcvars:
        if vcvars.is_file():
            return vcvars
    return None


@lru_cache(maxsize=1)
def _visual_studio_build_env_values() -> tuple[tuple[str, str], ...]:
    if shutil.which("cl") or shutil.which("cl.exe"):
        return ()
    vcvars = _known_vcvars64_path()
    if not vcvars:
        return ()
    command = f'call ""{vcvars}"" >nul && set'
    env = os.environ.copy()
    env.setdefault("VSCMD_SKIP_SENDTELEMETRY", "1")
    try:
        completed = subprocess.run(
            ["cmd.exe", "/d", "/c", command],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ()
    if completed.returncode != 0:
        return _manual_visual_studio_build_env_values()
    values: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.lower() == "path":
            key = "PATH"
        if key:
            values[key] = value
    return tuple(values.items()) if values else _manual_visual_studio_build_env_values()


@lru_cache(maxsize=1)
def _manual_visual_studio_build_env_values() -> tuple[tuple[str, str], ...]:
    build_tools_root = Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools")
    msvc_root = build_tools_root / "VC" / "Tools" / "MSVC"
    windows_kits_root = Path("C:/Program Files (x86)/Windows Kits/10")
    if not msvc_root.is_dir() or not windows_kits_root.is_dir():
        return ()
    msvc_versions = sorted((path for path in msvc_root.iterdir() if path.is_dir()), reverse=True)
    include_versions = sorted((path for path in (windows_kits_root / "include").iterdir() if path.is_dir()), reverse=True)
    lib_versions = sorted((path for path in (windows_kits_root / "lib").iterdir() if path.is_dir()), reverse=True)
    if not msvc_versions or not include_versions or not lib_versions:
        return ()
    msvc = msvc_versions[0]
    kit_include = include_versions[0]
    kit_lib = lib_versions[0]
    path_entries = [
        msvc / "bin" / "HostX64" / "x64",
        windows_kits_root / "bin" / kit_include.name / "x64",
        build_tools_root / "MSBuild" / "Current" / "Bin" / "amd64",
    ]
    include_entries = [
        msvc / "include",
        build_tools_root / "VC" / "Auxiliary" / "VS" / "include",
        kit_include / "ucrt",
        kit_include / "um",
        kit_include / "shared",
        kit_include / "winrt",
        kit_include / "cppwinrt",
    ]
    lib_entries = [
        msvc / "lib" / "x64",
        kit_lib / "ucrt" / "x64",
        kit_lib / "um" / "x64",
    ]
    return (
        ("PATH", os.pathsep.join(str(path) for path in path_entries if path.exists()) + os.pathsep + os.environ.get("PATH", "")),
        ("INCLUDE", os.pathsep.join(str(path) for path in include_entries if path.exists())),
        ("LIB", os.pathsep.join(str(path) for path in lib_entries if path.exists())),
        ("VCToolsInstallDir", str(msvc) + os.sep),
    )


def _visual_studio_build_env(base_env: dict[str, str]) -> dict[str, str]:
    values = _visual_studio_build_env_values()
    if not values:
        return base_env
    env = base_env.copy()
    for key, value in values:
        env[key] = value
    return env


def _python_module_dependency(module_name: str) -> SplatDependency:
    available = importlib.util.find_spec(module_name) is not None
    return SplatDependency(
        module_name,
        available,
        "python_module",
        "Installed in backend Python runtime."
        if available
        else f"Not importable from backend Python runtime; this is acceptable if Nerfstudio CLIs run from a separate environment.",
    )


def _python_runtime_dependency() -> SplatDependency:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    expected = sys.version_info >= (3, 8)
    detail = (
        f"Backend Python runtime is {version}. Nerfstudio should still be installed in an isolated "
        "environment with a tested Python/PyTorch/CUDA/gsplat/MSVC combination."
    )
    return SplatDependency("backend-python", expected, "python_runtime", detail)


def _nerfstudio_env_module_dependency(name: str, python_path: str | None, module_name: str) -> SplatDependency:
    if not python_path:
        return SplatDependency(
            name,
            False,
            "python_module",
            f"Optional: ROOMSPLAT_NERFSTUDIO_PYTHON_PATH is not configured, so {module_name} was not checked in the Nerfstudio environment.",
        )
    candidate = Path(python_path).expanduser()
    if not candidate.is_file():
        return SplatDependency(name, False, "python_module", f"Configured Nerfstudio Python was not found: {python_path}")
    command = [str(candidate.resolve()), "-c", f"import {module_name}; print(getattr({module_name}, '__version__', 'installed'))"]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True, timeout=30)
    except OSError as exc:
        return SplatDependency(name, False, "python_module", f"{module_name} import check could not start: {exc}")
    except subprocess.TimeoutExpired:
        return SplatDependency(name, False, "python_module", f"{module_name} import check timed out in configured Nerfstudio Python.")
    if completed.returncode == 0:
        version = (completed.stdout or "").strip() or "installed"
        return SplatDependency(name, True, "python_module", f"{module_name} import succeeded in configured Nerfstudio Python: {version}")
    detail = (completed.stderr or completed.stdout or "").strip()
    return SplatDependency(name, False, "python_module", f"{module_name} import failed in configured Nerfstudio Python: {detail or f'exit code {completed.returncode}'}")


def _next_steps(blockers: Sequence[str]) -> tuple[str, ...]:
    if not blockers:
        return (
            "Run reconstruct_splat on a small extracted-frame project first.",
            "Inspect reconstruction/splat.ply in the browser splat viewer after export.",
        )
    return (
        "Create an isolated Nerfstudio environment with a tested Python/PyTorch/CUDA/gsplat/MSVC combination.",
        "On Windows, install Visual Studio C++ Build Tools and CUDA Toolkit/nvcc compatible with the selected PyTorch and gsplat versions.",
        "Verify ns-process-data, ns-train, ns-export, torch, nerfstudio, gsplat, nvcc, COLMAP, and FFmpeg from that environment.",
        "Set ROOMSPLAT_NERFSTUDIO_BIN_DIR and optionally ROOMSPLAT_NERFSTUDIO_PYTHON_PATH, or set the three ROOMSPLAT_NS_*_PATH command overrides.",
        "Use a COLMAP build compatible with the installed Nerfstudio process-data flags; Nerfstudio 1.1.5 expects the older SiftExtraction.use_gpu flag.",
    )
