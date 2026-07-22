from __future__ import annotations

import json
import time
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.config import AppConfig
from app.main import app
from app.services.export_service import ArtifactService
from app.services.job_store import JobStore
from app.services.project_store import ProjectStore
from app.workers.local_worker import LocalWorker


def test_jobs_api_runs_learned_geometry_import(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Learned API import"}).json()
    project_dir = tmp_path / "data" / project["id"]
    _write_project_frames(project_dir, count=2)
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir)

    response = client.post(
        f"/projects/{project['id']}/jobs",
        json={
            "job_type": "import_learned_geometry",
            "params": {"source_dir": str(source_dir), "source_adapter": "lingbot-map-bss", "primary_ply": "points.ply"},
        },
    )

    assert response.status_code == 201
    completed = _wait_for_job(client, project["id"], response.json()["id"])
    assert completed["status"] == "succeeded"
    assert completed["result"]["artifact_type"] == "learned_geometry_bundle"

    artifacts = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"]
    labels = {artifact["relative_path"]: artifact["artifact_type"] for artifact in artifacts}
    assert labels["reconstruction/learned-point-cloud.ply"] == "predicted_point_cloud_ply"


def test_worker_preflights_learned_geometry_output(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Learned preflight")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=3)
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir, frame_indices=[0, 2])
    job_store = JobStore(project_store)
    job = job_store.create_job(
        project.id,
        "learned_geometry_preflight",
        {"source_dir": str(source_dir), "source_adapter": "lingbot-map-bss", "primary_ply": "points.ply"},
    )

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["status"] == "ready"
    assert completed.result["source_adapter"] == "lingbot-map-bss"
    assert completed.result["frame_count"] == 2
    assert completed.result["capabilities"] == {"depth": True, "confidence": True, "mask": False, "pointmap": True}
    assert {artifact["artifact_type"] for artifact in completed.result["expected_outputs"]} == {
        "learned_geometry_bundle",
        "predicted_point_cloud_ply",
    }


def test_worker_imports_learned_geometry_bundle_and_labels_artifacts(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Learned import")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=3)
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir, frame_indices=[0, 2])
    job_store = JobStore(project_store)
    job = job_store.create_job(
        project.id,
        "import_learned_geometry",
        {"source_dir": str(source_dir), "source_adapter": "lingbot-map-bss", "primary_ply": "points.ply"},
    )

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["artifact_type"] == "learned_geometry_bundle"
    assert completed.result["source_adapter"] == "lingbot-map-bss"
    assert completed.result["is_reconstruction"] is False
    assert completed.result["not_reconstruction"] is True
    assert completed.result["frame_index_map"] == [
        {"bundle_frame_index": 0, "source_frame_index": 0, "source_frame": "frames/frame_000001.png"},
        {"bundle_frame_index": 1, "source_frame_index": 2, "source_frame": "frames/frame_000003.png"},
    ]
    assert completed.result["capabilities"]["pointmap"] is True
    assert completed.result["cameras"][1]["position"] == {"x": 1.0, "y": 0.0, "z": 0.0}
    assert completed.result["intrinsics"][0]["width"] == 8
    sidecar_types = {sidecar["sidecar_type"] for sidecar in completed.result["sidecars"]}
    assert sidecar_types >= {"metadata", "depth", "confidence", "pointmap", "intrinsics", "trajectory"}
    assert (project_dir / "reconstruction" / "learned-point-cloud.ply").read_text(encoding="utf-8") == _tiny_ply()
    assert (project_dir / "metadata" / "geometry_bundle.json").is_file()

    artifacts = ArtifactService(project_store).list_artifacts(project.id)
    labels = {artifact.relative_path: artifact.artifact_type for artifact in artifacts}
    assert labels["reconstruction/learned-point-cloud.ply"] == "predicted_point_cloud_ply"
    assert labels["metadata/geometry_bundle.json"] == "learned_geometry_bundle"


def test_import_learned_geometry_rejects_project_without_extracted_frames(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("No frames")
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "import_learned_geometry", {"source_dir": str(source_dir)})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "failed"
    assert completed.error == "No extracted frames metadata was found. Extract frames before importing learned geometry."


def test_import_learned_geometry_rejects_missing_primary_ply(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Missing primary")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=2)
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir)
    (source_dir / "points.ply").unlink()
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "import_learned_geometry", {"source_dir": str(source_dir)})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "failed"
    assert "primary PLY was not found" in completed.error
    assert not (project_dir / "reconstruction" / "learned-point-cloud.ply").exists()


def test_import_learned_geometry_rejects_incomplete_source_manifest(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Incomplete source")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=2)
    source_dir = tmp_path / "learned-output"
    source_dir.mkdir()
    (source_dir / "points.ply").write_text(_tiny_ply(), encoding="utf-8")
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "import_learned_geometry", {"source_dir": str(source_dir)})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "failed"
    assert ".complete.json" in completed.error
    assert not (project_dir / "metadata" / "geometry_bundle.json").exists()


def test_import_learned_geometry_rejects_escaped_primary_path(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Escaped source")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=2)
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "import_learned_geometry", {"source_dir": str(source_dir), "primary_ply": "../outside.ply"})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "failed"
    assert "escaped source_dir" in completed.error
    assert not (project_dir / "reconstruction" / "learned-point-cloud.ply").exists()


def test_import_learned_geometry_rejects_missing_declared_sidecar(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Missing sidecar")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=2)
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir)
    for path in (source_dir / "depth").glob("*"):
        path.unlink()
    (source_dir / "depth").rmdir()
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "import_learned_geometry", {"source_dir": str(source_dir)})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "failed"
    assert "depth" in completed.error
    assert not (project_dir / "metadata" / "geometry_bundle.json").exists()


def test_import_learned_geometry_rejects_frame_index_outside_extracted_frames(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Bad frame map")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=2)
    source_dir = tmp_path / "learned-output"
    _write_learned_output(source_dir, frame_indices=[0, 8])
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "import_learned_geometry", {"source_dir": str(source_dir)})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "failed"
    assert "missing extracted frame index 8" in completed.error


def _wait_for_job(client: TestClient, project_id: str, job_id: str) -> dict:
    deadline = time.time() + 5
    while time.time() < deadline:
        response = client.get(f"/projects/{project_id}/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["status"] in {"succeeded", "failed"}:
            return job
        time.sleep(0.05)
    raise AssertionError("Job did not finish before timeout.")


def _write_project_frames(project_dir: Path, *, count: int) -> None:
    frames_dir = project_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        image = Image.new("RGB", (8, 6), (index * 30, index * 20, index * 10))
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        (frames_dir / f"frame_{index + 1:06d}.png").write_bytes(buffer.getvalue())
    metadata = {
        "project_id": project_dir.name,
        "source_video": "input/tiny.gif",
        "frames_dir": "frames",
        "fps": 10.0,
        "frame_count": count,
        "extracted_frame_count": count,
        "extraction_stride": 1,
        "width": 8,
        "height": 6,
        "extracted_at": "2026-07-22T00:00:00+00:00",
    }
    (project_dir / "metadata" / "frame_extraction.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _write_learned_output(source_dir: Path, *, frame_indices: list[int] | None = None) -> None:
    source_dir.mkdir(parents=True)
    (source_dir / ".complete.json").write_text(
        json.dumps(
            {
                "completed_at": "2026-07-22T00:00:00",
                "metadata": {
                    "frame_keys": ["depth", "confidence", "pose", "intrinsics", "points"],
                    "global_keys": ["points"],
                    "frame_index_map": frame_indices or [0, 1],
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
