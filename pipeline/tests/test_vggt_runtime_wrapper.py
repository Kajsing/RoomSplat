from __future__ import annotations

import subprocess
import sys
from argparse import Namespace
from pathlib import Path

import pytest
from PIL import Image

from pipeline.scripts.run_vggt_runtime import (
    VggtRuntimeError,
    choose_vggt_resolution,
    flatten_points_for_ply,
    parse_frame_index_map,
    write_ascii_ply,
    write_completion_json,
    write_intrinsics_txt,
    write_sampling_json,
    write_traj_txt,
)


def test_vggt_runtime_wrapper_help_exposes_roomsplat_contract() -> None:
    completed = subprocess.run(
        [sys.executable, "pipeline/scripts/run_vggt_runtime.py", "--help"],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 0
    assert "--frames-dir" in completed.stdout
    assert "--output-dir" in completed.stdout
    assert "--checkpoint" in completed.stdout
    assert "--frame-index-map" in completed.stdout


def test_vggt_runtime_wrapper_dry_run_writes_blocked_diagnostics(tmp_path) -> None:
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir()
    Image.new("RGB", (4, 4), (255, 0, 0)).save(frames_dir / "frame_000000.png")
    checkpoint = tmp_path / "model.pt"
    checkpoint.write_bytes(b"not loaded in dry-run")
    output_dir = tmp_path / "out"

    completed = subprocess.run(
        [
            sys.executable,
            "pipeline/scripts/run_vggt_runtime.py",
            "--frames-dir",
            str(frames_dir),
            "--output-dir",
            str(output_dir),
            "--checkpoint",
            str(checkpoint),
            "--max-frames",
            "1",
            "--image-max-size",
            "518",
            "--precision",
            "fp16",
            "--frame-index-map",
            "3",
            "--dry-run",
        ],
        capture_output=True,
        encoding="utf-8",
        check=False,
    )

    assert completed.returncode == 2
    assert "ROOMSPLAT_VGGT_BLOCKED" in completed.stderr
    assert (output_dir / "blocked_vggt_runtime.json").is_file()
    assert not (output_dir / ".complete.json").exists()
    assert not (output_dir / "points.ply").exists()


def test_parse_frame_index_map_matches_selected_frame_count() -> None:
    assert parse_frame_index_map("0, 2, 4", 3) == [0, 2, 4]
    with pytest.raises(VggtRuntimeError, match="contains 2 entries"):
        parse_frame_index_map("0,1", 3)
    with pytest.raises(VggtRuntimeError, match="negative"):
        parse_frame_index_map("0,-1", 2)


def test_choose_vggt_resolution_uses_vggt_default_when_budget_allows() -> None:
    assert choose_vggt_resolution(768) == 518
    assert choose_vggt_resolution(512) == 504
    with pytest.raises(VggtRuntimeError, match="at least 224"):
        choose_vggt_resolution(128)


def test_flatten_points_for_ply_filters_confidence_and_samples_deterministically() -> None:
    points = [[[[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]]]
    colors = [[[[10, 0, 0], [20, 0, 0], [30, 0, 0], [40, 0, 0]]]]
    confidence = [[[0.1, 0.9, 0.8, 0.7]]]

    exported_points, exported_colors = flatten_points_for_ply(points, colors, confidence, confidence_threshold=0.5, max_points=2)

    assert exported_points == [(1.0, 0.0, 0.0), (3.0, 0.0, 0.0)]
    assert exported_colors == [(20, 0, 0), (40, 0, 0)]


def test_vggt_output_files_match_learned_geometry_import_contract(tmp_path) -> None:
    write_ascii_ply(tmp_path / "points.ply", [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)], [(255, 0, 0), (0, 255, 0)])
    write_traj_txt(tmp_path / "traj.txt", [[[1, 0, 0, 0], [0, 1, 0, 2], [0, 0, 1, 0]]])
    write_intrinsics_txt(tmp_path / "intrinsics.txt", [[[6, 0, 3], [0, 6, 3], [0, 0, 1]]], 518)
    write_sampling_json(tmp_path / "sampling.json", [Path("frame_000000.png")], [7], {"adapter": "vggt", "point_count": 2})
    write_completion_json(tmp_path / ".complete.json", [7], frame_keys=["pose", "intrinsics"])

    assert "element vertex 2" in (tmp_path / "points.ply").read_text(encoding="utf-8")
    assert "0 1 0 0 0 0 1 0 -2" in (tmp_path / "traj.txt").read_text(encoding="utf-8")
    assert "0 6 6 3 3 518 518" in (tmp_path / "intrinsics.txt").read_text(encoding="utf-8")
    completion = (tmp_path / ".complete.json").read_text(encoding="utf-8")
    assert '"frame_keys": [' in completion
    assert '"global_keys": [' in completion
    assert '"points"' in completion
