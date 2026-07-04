from __future__ import annotations

import subprocess
from pathlib import Path

from pipeline.adapters.nerfstudio_splat_runner import (
    NerfstudioSplatPaths,
    NerfstudioSplatRunner,
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


def test_nerfstudio_splat_runner_builds_argument_list_commands(tmp_path) -> None:
    bin_dir = _write_fake_bin(tmp_path)
    paths = _paths(tmp_path)
    runner = NerfstudioSplatRunner(nerfstudio_bin_dir=str(bin_dir))

    process_command, train_command, export_command = runner.build_commands(paths, method="splatfacto", max_iterations=3000)

    assert all(isinstance(command, list) for command in [process_command, train_command, export_command])
    assert process_command[1] == "images"
    assert str(paths.frames_dir) in process_command
    assert train_command[1] == "splatfacto"
    assert "--max-num-iterations" in train_command
    assert export_command[1] == "gaussian-splat"
    assert "<config.yml>" in export_command


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
