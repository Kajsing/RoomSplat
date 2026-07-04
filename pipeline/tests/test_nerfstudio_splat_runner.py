from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pipeline.adapters.nerfstudio_splat_runner import (
    NerfstudioSplatPaths,
    NerfstudioSplatRunner,
    _infer_cuda_home,
    _infer_nerfstudio_env_prefix,
    find_exported_splat_ply,
    find_latest_config,
)


def test_nerfstudio_splat_runner_reports_missing_cli_dependencies(tmp_path) -> None:
    runner = NerfstudioSplatRunner(nerfstudio_bin_dir=str(tmp_path / "missing-bin"))

    readiness = runner.assess()

    assert readiness.status == "blocked_missing_dependencies"
    assert readiness.is_ready is False
    assert {"ns-process-data", "ns-train", "ns-export"}.issubset(
        {dependency.name for dependency in readiness.dependencies if not dependency.available}
    )
    assert readiness.next_steps


def test_nerfstudio_splat_runner_reports_supporting_tool_paths(tmp_path) -> None:
    bin_dir = _write_fake_bin(tmp_path)
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    ffmpeg = tools_dir / "ffmpeg.exe"
    colmap = tools_dir / "colmap.exe"
    ffmpeg.write_text("placeholder", encoding="utf-8")
    colmap.write_text("placeholder", encoding="utf-8")
    runner = NerfstudioSplatRunner(
        nerfstudio_bin_dir=str(bin_dir),
        ffmpeg_path=str(ffmpeg),
        colmap_path=str(colmap),
    )

    readiness = runner.assess()
    dependencies = {dependency.name: dependency for dependency in readiness.dependencies}

    assert dependencies["backend-python"].available is True
    assert dependencies["backend-python"].kind == "python_runtime"
    assert dependencies["conda"].kind == "executable"
    assert dependencies["nerfstudio-env-torch"].kind == "python_module"
    assert dependencies["ffmpeg"].available is True
    assert dependencies["colmap"].available is True
    assert dependencies["ffmpeg"].detail.endswith("ffmpeg.exe")
    assert dependencies["colmap"].detail.endswith("colmap.exe")


def test_nerfstudio_splat_runner_reports_configured_env_nvcc(tmp_path) -> None:
    env_dir = tmp_path / "nerfstudio-env"
    bin_dir = env_dir / "Scripts"
    cuda_bin = env_dir / "bin"
    bin_dir.mkdir(parents=True)
    cuda_bin.mkdir()
    for name in ["ns-process-data.exe", "ns-train.exe", "ns-export.exe"]:
        (bin_dir / name).write_text("placeholder", encoding="utf-8")
    (cuda_bin / "nvcc.exe").write_text("placeholder", encoding="utf-8")
    python_path = env_dir / "python.exe"
    python_path.write_text("placeholder", encoding="utf-8")

    runner = NerfstudioSplatRunner(
        nerfstudio_bin_dir=str(bin_dir),
        nerfstudio_python_path=str(python_path),
    )

    readiness = runner.assess()
    dependencies = {dependency.name: dependency for dependency in readiness.dependencies}

    assert dependencies["nerfstudio-env-nvcc"].available is True
    assert dependencies["nerfstudio-env-nvcc"].detail.endswith("nvcc.exe")


def test_nerfstudio_splat_runner_checks_configured_env_python(tmp_path) -> None:
    runner = NerfstudioSplatRunner(
        nerfstudio_bin_dir=str(_write_fake_bin(tmp_path)),
        nerfstudio_python_path=sys.executable,
    )

    readiness = runner.assess()
    dependencies = {dependency.name: dependency for dependency in readiness.dependencies}

    assert "configured Nerfstudio Python" in dependencies["nerfstudio-env-torch"].detail
    assert dependencies["nerfstudio-env-torch"].kind == "python_module"


def test_nerfstudio_splat_runner_builds_argument_list_commands(tmp_path) -> None:
    bin_dir = _write_fake_bin(tmp_path)
    paths = _paths(tmp_path)
    colmap_path = tmp_path / "tools" / "COLMAP.bat"
    colmap_path.parent.mkdir()
    colmap_path.write_text("placeholder", encoding="utf-8")
    runner = NerfstudioSplatRunner(nerfstudio_bin_dir=str(bin_dir), colmap_path=str(colmap_path))

    process_command, train_command, export_command = runner.build_commands(paths, method="splatfacto", max_iterations=3000)

    assert all(isinstance(command, list) for command in [process_command, train_command, export_command])
    assert process_command[1] == "images"
    assert str(paths.frames_dir) in process_command
    assert "--no-gpu" in process_command
    assert process_command[-2:] == ["--colmap-cmd", str(colmap_path)]
    assert train_command[1] == "splatfacto"
    assert "--viewer.quit-on-train-completion" in train_command
    assert "--max-num-iterations" in train_command
    assert export_command[1] == "gaussian-splat"
    assert "<config.yml>" in export_command


def test_nerfstudio_splat_runner_subprocess_env_prepends_env_paths(tmp_path, monkeypatch) -> None:
    env_dir = tmp_path / "nerfstudio-env"
    for name in ["bin", "Scripts", "Library/bin"]:
        (env_dir / name).mkdir(parents=True)
    python_path = env_dir / "python.exe"
    python_path.write_text("placeholder", encoding="utf-8")
    tool_dir = tmp_path / "tools" / "colmap" / "bin"
    tool_dir.mkdir(parents=True)
    colmap_path = tool_dir / "colmap.exe"
    colmap_path.write_text("placeholder", encoding="utf-8")
    monkeypatch.setenv("PATH", "C:\\Windows\\System32")

    runner = NerfstudioSplatRunner(nerfstudio_python_path=str(python_path), colmap_path=str(colmap_path))

    subprocess_env = runner._subprocess_env()

    path_parts = subprocess_env["PATH"].split(";")
    assert path_parts[:5] == [
        str(env_dir),
        str(env_dir / "bin"),
        str(env_dir / "Scripts"),
        str(env_dir / "Library" / "bin"),
        str(tool_dir),
    ]
    assert subprocess_env["CUDA_HOME"] == str(env_dir)
    assert subprocess_env["CUDA_PATH"] == str(env_dir)
    assert subprocess_env["PYTHONUTF8"] == "1"
    assert subprocess_env["PYTHONIOENCODING"] == "utf-8"
    assert subprocess_env["DISTUTILS_USE_SDK"] == "1"
    assert (
        subprocess_env["NVCC_PREPEND_FLAGS"]
        == "-allow-unsupported-compiler -D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH -DCCCL_IGNORE_MSVC_TRADITIONAL_PREPROCESSOR_WARNING"
    )
    assert subprocess_env["CL"] == "/D_ALLOW_COMPILER_AND_STL_VERSION_MISMATCH /Zc:preprocessor"


def test_infer_nerfstudio_env_prefix_from_python_or_bin_dir(tmp_path) -> None:
    env_dir = tmp_path / "nerfstudio-env"

    assert _infer_nerfstudio_env_prefix(str(env_dir / "python.exe"), None) == env_dir
    assert _infer_nerfstudio_env_prefix(None, str(env_dir / "Scripts")) == env_dir


def test_infer_cuda_home_prefers_conda_forge_library_layout(tmp_path) -> None:
    env_dir = tmp_path / "nerfstudio-env"
    library_bin = env_dir / "Library" / "bin"
    library_bin.mkdir(parents=True)
    (library_bin / "nvcc.exe").write_text("placeholder", encoding="utf-8")

    assert _infer_cuda_home(env_dir) == env_dir / "Library"


def test_nerfstudio_splat_runner_contract_with_mocked_commands(tmp_path) -> None:
    bin_dir = _write_fake_bin(tmp_path)
    paths = _paths(tmp_path)
    commands_seen: list[list[str]] = []

    def fake_run(command):
        commands_seen.append(list(command))
        executable = Path(command[0]).name
        if executable.startswith("ns-process-data"):
            paths.dataset_dir.mkdir(parents=True, exist_ok=True)
        if executable.startswith("ns-train"):
            config_path = paths.output_dir / "splatfacto" / "run" / "config.yml"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("method_name: splatfacto\n", encoding="utf-8")
        if executable.startswith("ns-export"):
            paths.export_dir.mkdir(parents=True, exist_ok=True)
            (paths.export_dir / "splat.ply").write_text("ply\nformat ascii 1.0\nend_header\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    runner = NerfstudioSplatRunner(nerfstudio_bin_dir=str(bin_dir), command_runner=fake_run)

    result = runner.run(paths, method="splatfacto", max_iterations=25)

    assert [Path(command[0]).stem for command in commands_seen] == ["ns-process-data", "ns-train", "ns-export"]
    assert "--output-dir" in commands_seen[2]
    assert str(paths.export_dir) in commands_seen[2]
    assert "<config.yml>" not in commands_seen[2]
    assert result.config_path.name == "config.yml"
    assert result.exported_ply.name == "splat.ply"
    assert paths.final_splat_ply.is_file()
    assert result.command_count == 3


def test_find_latest_config_and_exported_splat(tmp_path) -> None:
    older = tmp_path / "old" / "config.yml"
    newer = tmp_path / "new" / "config.yml"
    older.parent.mkdir()
    newer.parent.mkdir()
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")
    ply = tmp_path / "exports" / "splat.ply"
    ply.parent.mkdir()
    ply.write_text("ply", encoding="utf-8")

    assert find_latest_config(tmp_path) in {older, newer}
    assert find_exported_splat_ply(ply.parent) == ply


def _write_fake_bin(tmp_path: Path) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in ["ns-process-data.exe", "ns-train.exe", "ns-export.exe"]:
        (bin_dir / name).write_text("placeholder", encoding="utf-8")
    return bin_dir


def _paths(tmp_path: Path) -> NerfstudioSplatPaths:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    return NerfstudioSplatPaths(
        frames_dir=frames_dir,
        dataset_dir=tmp_path / "dataset",
        output_dir=tmp_path / "output",
        export_dir=tmp_path / "export",
        final_splat_ply=tmp_path / "reconstruction" / "splat.ply",
    )
