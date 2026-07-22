import json
from pathlib import Path

import pytest

from pipeline.adapters.learned_geometry_import import (
    LearnedGeometryImportError,
    inspect_learned_geometry_output,
    learned_geometry_expected_sidecars,
    learned_geometry_import_assessment,
)


def test_inspect_learned_geometry_output_reads_lingbot_style_completion(tmp_path) -> None:
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir)

    summary = inspect_learned_geometry_output(source_dir)

    assert summary.primary_ply == source_dir / "points.ply"
    assert summary.frame_keys == ["confidence", "depth", "intrinsics", "points", "pose"]
    assert summary.global_keys == ["points"]
    assert summary.frame_index_map == [0, 2]
    assert summary.capabilities == {"depth": True, "confidence": True, "mask": False, "pointmap": True}
    assert {sidecar.sidecar_type for sidecar in summary.sidecars} >= {"metadata", "depth", "confidence", "pointmap", "intrinsics", "trajectory"}


def test_inspect_learned_geometry_output_rejects_incomplete_source(tmp_path) -> None:
    source_dir = tmp_path / "incomplete"
    source_dir.mkdir()
    (source_dir / "points.ply").write_text(_tiny_ply(), encoding="utf-8")

    with pytest.raises(LearnedGeometryImportError, match=".complete.json"):
        inspect_learned_geometry_output(source_dir)


def test_inspect_learned_geometry_output_rejects_escaped_primary_path(tmp_path) -> None:
    source_dir = tmp_path / "source"
    _write_learned_output(source_dir)

    with pytest.raises(LearnedGeometryImportError, match="escaped"):
        inspect_learned_geometry_output(source_dir, "../outside.ply")


def test_inspect_learned_geometry_output_rejects_declared_missing_sidecar(tmp_path) -> None:
    source_dir = tmp_path / "source"
    _write_learned_output(source_dir)
    for path in (source_dir / "depth").glob("*"):
        path.unlink()
    (source_dir / "depth").rmdir()

    with pytest.raises(LearnedGeometryImportError, match="depth"):
        inspect_learned_geometry_output(source_dir)


def test_learned_geometry_import_assessment_declares_contract_outputs() -> None:
    assessment = learned_geometry_import_assessment()

    assert assessment.status == "ready"
    assert {artifact.artifact_type for artifact in assessment.expected_outputs} == {
        "learned_geometry_bundle",
        "predicted_point_cloud_ply",
    }
    assert learned_geometry_expected_sidecars(["pose", "intrinsics", "depth", "points"]) == [
        ".complete.json",
        "traj.txt",
        "intrinsics.txt",
        "depth/",
        "points/",
    ]


def _write_learned_output(source_dir: Path) -> None:
    source_dir.mkdir(parents=True)
    (source_dir / ".complete.json").write_text(
        json.dumps(
            {
                "completed_at": "2026-07-22T00:00:00",
                "metadata": {
                    "frame_keys": ["depth", "confidence", "pose", "intrinsics", "points"],
                    "global_keys": ["points"],
                    "frame_index_map": [0, 2],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (source_dir / "points.ply").write_text(_tiny_ply(), encoding="utf-8")
    (source_dir / "traj.txt").write_text(
        "\n".join(
            [
                "# frame_idx r00 r01 r02 tx r10 r11 r12 ty r20 r21 r22 tz",
                "0 1 0 0 0 0 1 0 0 0 0 1 0",
                "1 1 0 0 1 0 1 0 0 0 0 1 0",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (source_dir / "intrinsics.txt").write_text(
        "\n".join(
            [
                "# frame_idx fx fy cx cy width height",
                "0 6.0 6.0 4.0 3.0 8 6",
                "1 6.0 6.0 4.0 3.0 8 6",
                "",
            ]
        ),
        encoding="utf-8",
    )
    for folder in ("depth", "confidence", "points"):
        (source_dir / folder).mkdir()
        (source_dir / folder / "000000.exr").write_bytes(b"sidecar")


def _tiny_ply() -> str:
    return "\n".join(
        [
            "ply",
            "format ascii 1.0",
            "element vertex 1",
            "property float x",
            "property float y",
            "property float z",
            "end_header",
            "0 0 0",
            "",
        ]
    )
