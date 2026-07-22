from __future__ import annotations

import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.config import AppConfig
from app.services.export_service import ArtifactService
from app.services.job_store import JobStore
from app.services.project_store import ProjectStore
from app.workers.local_worker import LocalWorker


def test_worker_learned_runtime_preflight_reports_blocked_without_command_or_checkpoint(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Runtime preflight")
    _write_project_frames(tmp_path / "data" / project.id, count=2)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "learned_runtime_preflight", {"max_frames": 1})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["job_type"] == "learned_runtime_preflight"
    assert completed.result["status"] in {"blocked_missing_checkpoint", "blocked_missing_dependencies"}
    assert completed.result["generated_data_rules"]["no_auto_downloads"] is True
    assert (tmp_path / "data" / project.id / "metadata" / "learned_runtime_preflight.json").is_file()


def test_worker_learned_runtime_smoke_blocks_without_fake_artifacts(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Runtime blocked")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=2)
    job_store = JobStore(project_store)
    job = job_store.create_job(project.id, "learned_runtime_smoke", {"max_frames": 1})

    completed = LocalWorker(project_store, job_store, AppConfig(data_dir=tmp_path / "data")).run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["imported"] is False
    assert completed.result["output_path"] is None
    assert not (project_dir / "reconstruction" / "learned-point-cloud.ply").exists()
    assert not (project_dir / "metadata" / "geometry_bundle.json").exists()


def test_worker_learned_runtime_smoke_imports_fake_local_runtime_output(tmp_path) -> None:
    project_store = ProjectStore(tmp_path / "data")
    project = project_store.create_project("Runtime success")
    project_dir = tmp_path / "data" / project.id
    _write_project_frames(project_dir, count=3)
    model_root = tmp_path / "data" / "models"
    model_root.mkdir(parents=True)
    checkpoint = model_root / "fake.pt"
    checkpoint.write_bytes(b"fake checkpoint")
    digest = hashlib.sha256(b"fake checkpoint").hexdigest()
    runtime_script = tmp_path / "fake_runtime.py"
    runtime_script.write_text(_fake_runtime_script(), encoding="utf-8")
    job_store = JobStore(project_store)
    job = job_store.create_job(
        project.id,
        "learned_runtime_smoke",
        {"max_frames": 2, "frame_step": 2, "image_max_size": 256, "precision": "fp16", "adapter": "fake-learned-runtime"},
    )

    completed = LocalWorker(
        project_store,
        job_store,
        AppConfig(
            data_dir=tmp_path / "data",
            learned_runtime_command=sys.executable,
            learned_runtime_args=str(runtime_script),
            learned_checkpoint_path="fake.pt",
            learned_checkpoint_sha256=digest,
            learned_model_root=model_root,
            learned_min_free_vram_mb=1,
            learned_runtime_timeout_seconds=30,
        ),
    ).run_job(project.id, job.id)

    assert completed.status == "succeeded"
    assert completed.result is not None
    assert completed.result["artifact_type"] == "learned_geometry_bundle"
    assert completed.result["runtime_status"] == "succeeded"
    assert completed.result["source_adapter"] == "fake-learned-runtime"
    assert completed.result["frame_count"] == 2
    assert completed.result["frame_index_map"] == [
        {"bundle_frame_index": 0, "source_frame_index": 0, "source_frame": "frames/frame_000001.png"},
        {"bundle_frame_index": 1, "source_frame_index": 2, "source_frame": "frames/frame_000003.png"},
    ]
    assert (project_dir / "reconstruction" / "learned-point-cloud.ply").is_file()
    assert (project_dir / "metadata" / "geometry_bundle.json").is_file()
    assert "fake.pt" not in (project_dir / "metadata" / "geometry_bundle.json").read_text(encoding="utf-8")

    artifacts = ArtifactService(project_store).list_artifacts(project.id)
    labels = {artifact.relative_path: artifact.artifact_type for artifact in artifacts}
    assert labels["reconstruction/learned-point-cloud.ply"] == "predicted_point_cloud_ply"
    assert labels["metadata/geometry_bundle.json"] == "learned_geometry_bundle"


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


def _fake_runtime_script() -> str:
    return r'''
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--frames-dir", required=True)
parser.add_argument("--output-dir", required=True)
parser.add_argument("--checkpoint", required=True)
parser.add_argument("--max-frames", required=True)
parser.add_argument("--image-max-size", required=True)
parser.add_argument("--precision", required=True)
parser.add_argument("--frame-index-map", required=True)
parser.add_argument("--allow-cpu-offload", action="store_true")
args = parser.parse_args()
output = Path(args.output_dir)
output.mkdir(parents=True, exist_ok=True)
frame_indices = [int(value) for value in args.frame_index_map.split(",") if value]
(output / ".complete.json").write_text(json.dumps({
    "completed_at": "2026-07-22T00:00:00",
    "metadata": {
        "frame_keys": ["pose", "intrinsics"],
        "global_keys": ["points"],
        "frame_index_map": frame_indices,
    },
}, indent=2), encoding="utf-8")
(output / "points.ply").write_text("\n".join([
    "ply",
    "format ascii 1.0",
    "element vertex 2",
    "property float x",
    "property float y",
    "property float z",
    "end_header",
    "0 0 0",
    "1 0 0",
    "",
]), encoding="utf-8")
(output / "traj.txt").write_text("\n".join([
    "0 1 0 0 0 0 1 0 0 0 0 1 0",
    "1 1 0 0 1 0 1 0 0 0 0 1 0",
    "",
]), encoding="utf-8")
(output / "intrinsics.txt").write_text("\n".join([
    "0 6.0 6.0 4.0 3.0 8 6",
    "1 6.0 6.0 4.0 3.0 8 6",
    "",
]), encoding="utf-8")
'''
