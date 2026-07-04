from __future__ import annotations

import importlib.util
import shutil
import subprocess
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
        ffmpeg_path: str | None = None,
        colmap_path: str | None = None,
        command_runner: CommandRunner | None = None,
    ) -> None:
        self.ns_process_data_path = ns_process_data_path
        self.ns_train_path = ns_train_path
        self.ns_export_path = ns_export_path
        self.nerfstudio_bin_dir = nerfstudio_bin_dir
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
        ]
        train_command = [
            ns_train,
            method,
            "--data",
            str(paths.dataset_dir),
            "--output-dir",
            str(paths.output_dir),
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
            *export_command_template[:4],
            str(config_path),
            *export_command_template[5:],
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

    @staticmethod
    def _run_subprocess(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
        )


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


def _next_steps(blockers: Sequence[str]) -> tuple[str, ...]:
    if not blockers:
        return (
            "Run reconstruct_splat on a small extracted-frame project first.",
            "Inspect reconstruction/splat.ply in the browser splat viewer after export.",
        )
    return (
        "Create an isolated Nerfstudio environment with Python 3.8-3.10, PyTorch CUDA, CUDA toolkit, and Visual Studio C++ Build Tools.",
        "On Windows, run Nerfstudio install/training commands from a Visual Studio Developer Command Prompt when CUDA extensions need cl.exe.",
        "Install Nerfstudio and run ns-train splatfacto --help.",
        "Ensure ns-process-data, ns-train, and ns-export are on PATH or set ROOMSPLAT_NERFSTUDIO_BIN_DIR.",
        "Keep COLMAP and FFmpeg available for ns-process-data images/video processing.",
    )
