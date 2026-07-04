from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from pipeline.adapters.colmap_sparse_runner import (
    ColmapRunnerError,
    ColmapSparseReconstructionRunner,
    build_colmap_commands,
    build_colmap_paths,
    read_ascii_ply_vertex_count,
    resolve_colmap_executable,
)


def test_build_colmap_commands_uses_argument_lists_without_shell_strings(tmp_path) -> None:
    executable = str(tmp_path / "colmap.exe")
    frames_dir = tmp_path / "frames with spaces"
    workspace_dir = tmp_path / "workspace"
    output_ply = tmp_path / "reconstruction" / "sparse-point-cloud.ply"
    paths = build_colmap_paths(frames_dir, workspace_dir, output_ply)

    commands = build_colmap_commands(executable, paths, matcher="sequential", use_gpu=False)

    assert all(isinstance(command, list) for command in commands)
    assert all(command[0] == executable for command in commands)
    assert commands[0][1] == "feature_extractor"
    assert commands[1][1] == "sequential_matcher"
    assert str(frames_dir) in commands[0]
    assert str(frames_dir) in commands[2]
    assert "--FeatureExtraction.use_gpu" in commands[0]
    assert "--FeatureMatching.use_gpu" in commands[1]


def test_build_colmap_commands_rejects_unknown_matcher(tmp_path) -> None:
    paths = build_colmap_paths(tmp_path / "frames", tmp_path / "workspace", tmp_path / "out.ply")

    with pytest.raises(ColmapRunnerError, match="matcher"):
        build_colmap_commands("colmap", paths, matcher="bad;matcher", use_gpu=False)


def test_runner_contract_with_mocked_colmap_commands(tmp_path) -> None:
    colmap_exe = tmp_path / "colmap.exe"
    colmap_exe.write_text("placeholder", encoding="utf-8")
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    workspace_dir = tmp_path / "workspace"
    output_ply = tmp_path / "reconstruction" / "sparse-point-cloud.ply"
    commands_seen: list[list[str]] = []

    def fake_run(command):
        commands_seen.append(list(command))
        command_name = command[1]
        if command_name == "mapper":
            (workspace_dir / "sparse" / "0").mkdir(parents=True)
        if command_name == "model_converter" and command[-1] == "TXT":
            text_dir = Path(command[command.index("--output_path") + 1])
            text_dir.mkdir(parents=True, exist_ok=True)
            (text_dir / "images.txt").write_text(
                "\n".join(
                    [
                        "# images",
                        "1 1 0 0 0 0 0 0 1 frame_000001.png",
                        "0 0 -1",
                        "2 1 0 0 0 1 0 0 1 frame_000002.png",
                        "0 0 -1",
                        "3 1 0 0 0 2 0 0 1 frame_000003.png",
                        "0 0 -1",
                    ]
                ),
                encoding="utf-8",
            )
            (text_dir / "points3D.txt").write_text("1 0 0 0 255 0 0 1\n2 1 0 0 0 255 0 1\n", encoding="utf-8")
        if command_name == "model_converter" and command[-1] == "PLY":
            Path(command[command.index("--output_path") + 1]).write_text(_tiny_ply(2), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, "", "")

    runner = ColmapSparseReconstructionRunner(executable=str(colmap_exe), command_runner=fake_run)

    result = runner.run(frames_dir, workspace_dir, output_ply, matcher="exhaustive", use_gpu=False)

    assert [command[1] for command in commands_seen] == [
        "feature_extractor",
        "exhaustive_matcher",
        "mapper",
        "model_converter",
        "model_converter",
    ]
    assert result.registered_image_count == 3
    assert result.sparse_point_count == 2
    assert result.ply_point_count == 2
    assert result.output_ply == output_ply


def test_resolve_colmap_executable_reports_missing_configured_path(tmp_path) -> None:
    missing = tmp_path / "missing-colmap.exe"

    with pytest.raises(ColmapRunnerError, match="Configured COLMAP executable was not found"):
        resolve_colmap_executable(str(missing))


def test_read_ascii_ply_vertex_count(tmp_path) -> None:
    ply_path = tmp_path / "points.ply"
    ply_path.write_text(_tiny_ply(12), encoding="utf-8")

    assert read_ascii_ply_vertex_count(ply_path) == 12


def _tiny_ply(point_count: int) -> str:
    return "\n".join(
        [
            "ply",
            "format ascii 1.0",
            f"element vertex {point_count}",
            "property float x",
            "property float y",
            "property float z",
            "end_header",
            *(f"{index} 0 0" for index in range(point_count)),
            "",
        ]
    )
