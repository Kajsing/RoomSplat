from __future__ import annotations

import json
import time
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image
import pytest

from app.config import AppConfig
from app.main import app
from app.services.debug_frame_cloud import DebugFrameCloudService
from app.services.job_store import JobStore
from app.services.project_store import ProjectStore
from app.services.video_import import VideoImportService
from app.workers.local_worker import LocalWorker


def test_job_store_records_queued_and_running_states(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Jobs")
    job_store = JobStore(project_store)

    job = job_store.create_job(project.id, "frame_extraction", {"stride": 1})
    running = job_store.mark_running(project.id, job.id)

    assert job.status == "queued"
    assert running.status == "running"
    assert running.started_at is not None
    assert Path(running.log_path).read_text(encoding="utf-8").count("running") == 1


def test_worker_succeeds_frame_extraction_job_and_preserves_result(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Extract")
    VideoImportService(project_store).import_uploaded_video(
        project.id,
        "tiny.gif",
        _tiny_gif_bytes(frame_count=5),
        "image/gif",
    )
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "frame_extraction", {"stride": 2, "max_frames": 2})
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["extracted_frame_count"] == 2
    assert (tmp_path / project.id / "frames" / "frame_000001.png").is_file()
    assert "extracted 2 frames" in Path(completed.log_path).read_text(encoding="utf-8")


def test_worker_fails_job_and_preserves_error(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Failure")
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "frame_extraction", {})
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "failed"
    assert completed.error == "No imported video was found for this project."
    assert "failed: No imported video was found" in Path(completed.log_path).read_text(encoding="utf-8")


def test_worker_runs_reconstruction_spike_job(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Spike")
    frames_dir = tmp_path / project.id / "frames"
    _write_frames(frames_dir, count=4)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "reconstruction_spike", {})
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["selected_interim_path"] == "COLMAP or pycolmap poses -> Nerfstudio Splatfacto -> splat.ply"
    assert (tmp_path / project.id / "metadata" / "reconstruction_spike.json").is_file()


def test_worker_runs_debug_frame_cloud_job(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Frame cloud")
    project_dir = tmp_path / project.id
    _write_frames(project_dir / "frames", count=5)
    _write_frame_extraction_metadata(project_dir, frames_dir="frames", count=5)
    job_store = JobStore(project_store)
    job = job_store.create_job(
        project.id,
        "debug_frame_cloud",
        {"max_points": 120, "frame_step": 2, "arc_degrees": 80, "plane_width": 1.6},
    )
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["artifact_type"] == "debug_frame_cloud_ply"
    assert completed.result["mode"] == "debug"
    assert completed.result["not_reconstruction"] is True
    assert completed.result["sampled_points"] <= 120
    assert completed.result["source_frame_count"] == 5
    assert completed.result["frame_count"] == 3
    assert completed.result["params"] == {"max_points": 120, "frame_step": 2, "arc_degrees": 80.0, "plane_width": 1.6}
    assert [plane["frame_index"] for plane in completed.result["frame_planes"]] == [0, 1, 2]
    assert {plane["source_frame"] for plane in completed.result["frame_planes"]} == {
        "frames/frame_000001.png",
        "frames/frame_000003.png",
        "frames/frame_000005.png",
    }
    assert sum(plane["point_count"] for plane in completed.result["frame_planes"]) == completed.result["sampled_points"]
    ply_path = project_dir / "reconstruction" / "debug-frame-room.ply"
    metadata_path = project_dir / "metadata" / "debug_frame_cloud.json"
    assert ply_path.is_file()
    assert metadata_path.is_file()
    assert "not a reconstruction" in ply_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("params", "expected_error"),
    [
        ({"max_points": 50_001}, "max_points must be between 1 and 50000."),
        ({"frame_step": 0}, "frame_step must be at least 1."),
        ({"arc_degrees": 0}, "arc_degrees must be greater than 0 and at most 180."),
        ({"arc_degrees": 181}, "arc_degrees must be greater than 0 and at most 180."),
        ({"plane_width": 0}, "plane_width must be greater than 0 and at most 10."),
        ({"plane_width": 11}, "plane_width must be greater than 0 and at most 10."),
    ],
)
def test_worker_rejects_invalid_debug_frame_cloud_params(tmp_path, params, expected_error) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Frame cloud invalid params")
    project_dir = tmp_path / project.id
    _write_frames(project_dir / "frames", count=2)
    _write_frame_extraction_metadata(project_dir, frames_dir="frames", count=2)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "debug_frame_cloud", params)
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "failed"
    assert completed.error == expected_error


def test_debug_frame_cloud_output_is_deterministic_except_timestamp(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Frame cloud deterministic")
    project_dir = tmp_path / project.id
    _write_frames(project_dir / "frames", count=4)
    _write_frame_extraction_metadata(project_dir, frames_dir="frames", count=4)
    service = DebugFrameCloudService(project_store)

    first_metadata = service.generate(project.id, max_points=32, frame_step=1, arc_degrees=60, plane_width=1.25)
    first_ply = (project_dir / "reconstruction" / "debug-frame-room.ply").read_text(encoding="utf-8")
    second_metadata = service.generate(project.id, max_points=32, frame_step=1, arc_degrees=60, plane_width=1.25)
    second_ply = (project_dir / "reconstruction" / "debug-frame-room.ply").read_text(encoding="utf-8")

    assert first_ply == second_ply
    first_metadata.pop("generated_at")
    second_metadata.pop("generated_at")
    assert first_metadata == second_metadata


def test_worker_rejects_debug_frame_cloud_without_extracted_frames(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("No frames")
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "debug_frame_cloud", {})
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "failed"
    assert completed.error == "No extracted frames metadata was found. Extract frames before creating a debug 3D preview."


def test_worker_rejects_debug_frame_cloud_frames_dir_outside_project(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Frame cloud path safety")
    project_dir = tmp_path / project.id
    outside_frames = tmp_path / "outside"
    _write_frames(outside_frames, count=2)
    _write_frame_extraction_metadata(project_dir, frames_dir=str(outside_frames), count=2)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "debug_frame_cloud", {})
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "failed"
    assert completed.error == "Debug frame cloud path escaped the project directory."


def test_worker_rejects_reconstruction_frames_dir_outside_project(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Spike path safety")
    outside_frames = tmp_path / "outside"
    _write_frames(outside_frames, count=4)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "reconstruction_spike", {"frames_dir": str(outside_frames)})
    worker = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path))

    completed = worker.run_job(project.id, job.id)

    assert completed.status == "failed"
    assert completed.error == "Job path escaped the project directory."


def test_jobs_api_creates_and_polls_job(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "API jobs"}).json()
    client.post(
        f"/projects/{project['id']}/videos/upload",
        params={"filename": "tiny.gif"},
        content=_tiny_gif_bytes(frame_count=3),
        headers={"content-type": "image/gif"},
    )

    create_response = client.post(
        f"/projects/{project['id']}/jobs",
        json={"job_type": "frame_extraction", "params": {"stride": 1}},
    )

    assert create_response.status_code == 201
    job = create_response.json()
    assert job["status"] in {"queued", "running", "succeeded"}

    completed = _wait_for_job(client, project["id"], job["id"])
    assert completed["status"] == "succeeded"
    assert completed["result"]["extracted_frame_count"] == 3

    list_response = client.get(f"/projects/{project['id']}/jobs")
    assert list_response.status_code == 200
    assert list_response.json()["jobs"][0]["id"] == job["id"]


def test_job_metadata_is_durable_json(tmp_path) -> None:
    project_store = ProjectStore(tmp_path)
    project = project_store.create_project("Durable")
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "reconstruction_spike", {"example": True})

    job_path = tmp_path / project.id / "metadata" / "jobs" / f"{job.id}.json"
    stored = json.loads(job_path.read_text(encoding="utf-8"))

    assert stored["id"] == job.id
    assert stored["status"] == "queued"
    assert stored["params"] == {"example": True}
    assert (tmp_path / project.id / "metadata" / "jobs" / f"{job.id}.log").is_file()


def _wait_for_job(client: TestClient, project_id: str, job_id: str) -> dict:
    deadline = time.time() + 5
    while time.time() < deadline:
        response = client.get(f"/projects/{project_id}/jobs/{job_id}")
        if response.status_code == 404:
            time.sleep(0.05)
            continue
        assert response.status_code == 200
        job = response.json()
        if job["status"] in {"succeeded", "failed"}:
            return job
        time.sleep(0.05)
    raise AssertionError("Job did not finish before timeout.")


def _tiny_gif_bytes(frame_count: int) -> bytes:
    frames = []
    for index in range(frame_count):
        frame = Image.new("RGB", (8, 6), (index * 30, index * 20, index * 10))
        frames.append(frame)

    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )
    return output.getvalue()


def _write_frames(frames_dir: Path, count: int) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    for index in range(count):
        frame = Image.new("RGB", (8, 6), (index * 20, index * 10, index * 5))
        frame.save(frames_dir / f"frame_{index + 1:06d}.png")


def _write_frame_extraction_metadata(project_dir: Path, frames_dir: str, count: int) -> None:
    payload = {
        "project_id": project_dir.name,
        "source_video": "input/tiny.gif",
        "frames_dir": frames_dir,
        "fps": 10.0,
        "frame_count": count,
        "extracted_frame_count": count,
        "extraction_stride": 1,
        "width": 8,
        "height": 6,
        "extracted_at": "2026-07-04T00:00:00+00:00",
    }
    (project_dir / "metadata" / "frame_extraction.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
