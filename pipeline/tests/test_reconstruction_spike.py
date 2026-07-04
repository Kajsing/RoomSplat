import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from pipeline.adapters import ColmapPoseAdapter, ReconstructionInput


def test_reconstruction_spike_reports_adapter_contract(tmp_path) -> None:
    frames_dir = tmp_path / "frames"
    _write_frames(frames_dir, count=4)

    result = subprocess.run(
        [
            sys.executable,
            str(Path("pipeline/scripts/run_reconstruction_spike.py")),
            "--frames-dir",
            str(frames_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    report = json.loads(result.stdout)
    assert report["selected_interim_path"] == "COLMAP or pycolmap poses -> Nerfstudio Splatfacto -> splat.ply"
    assert report["input"]["frame_count"] == 4
    assert report["input"]["width"] == 8
    assert report["input"]["height"] == 6
    assert {adapter["adapter"] for adapter in report["adapters"]} == {
        "colmap",
        "nerfstudio-splatfacto",
        "gsplat",
        "open3d-debug",
    }
    assert {artifact["artifact_type"] for artifact in report["output_contract"]} == {
        "camera_poses",
        "point_cloud_ply",
        "splat_ply",
    }
    assert report["status"] in {
        "ready_to_attempt_interim_path",
        "stop_condition_missing_dependencies",
    }


def test_reconstruction_spike_write_report_for_project(tmp_path) -> None:
    project_dir = tmp_path / "project"
    frames_dir = project_dir / "frames"
    (project_dir / "metadata").mkdir(parents=True)
    _write_frames(frames_dir, count=3)

    subprocess.run(
        [
            sys.executable,
            str(Path("pipeline/scripts/run_reconstruction_spike.py")),
            "--project",
            str(project_dir),
            "--write-report",
            "--json",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    report_path = project_dir / "metadata" / "reconstruction_spike.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["project_dir"] == str(project_dir.resolve())
    assert report["input"]["frames_dir"] == str(frames_dir.resolve())


def test_reconstruction_spike_rejects_missing_frames(tmp_path) -> None:
    frames_dir = tmp_path / "empty-frames"
    frames_dir.mkdir()

    result = subprocess.run(
        [
            sys.executable,
            str(Path("pipeline/scripts/run_reconstruction_spike.py")),
            "--frames-dir",
            str(frames_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "No frame images found" in result.stderr


def test_colmap_adapter_declares_pose_and_point_cloud_outputs(tmp_path) -> None:
    adapter = ColmapPoseAdapter()
    assessment = adapter.assess(
        ReconstructionInput(
            frames_dir=tmp_path,
            frame_count=3,
            width=8,
            height=6,
        )
    )

    assert assessment.adapter == "colmap"
    assert {artifact.artifact_type for artifact in assessment.expected_outputs} == {
        "camera_poses",
        "point_cloud_ply",
    }


def _write_frames(frames_dir: Path, count: int) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        frame = Image.new("RGB", (8, 6), (index * 20, index * 10, index * 5))
        frame.save(frames_dir / f"frame_{index + 1:06d}.png")
