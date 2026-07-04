from __future__ import annotations

import json
import time
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.config import AppConfig
from app.main import app
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
