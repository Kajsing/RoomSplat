from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.models.schemas import JobResponse
from app.services.frame_extraction import FrameExtractionService
from app.services.job_store import JobStore
from app.services.project_store import ProjectStore

from pipeline.scripts.run_reconstruction_spike import build_report, inspect_frames, write_report


class LocalWorker:
    def __init__(self, project_store: ProjectStore, job_store: JobStore, config: AppConfig) -> None:
        self.project_store = project_store
        self.job_store = job_store
        self.config = config

    def run_job(self, project_id: str, job_id: str) -> JobResponse:
        job = self.job_store.mark_running(project_id, job_id)
        try:
            self.job_store.append_log(project_id, job_id, f"executing {job.job_type}")
            result = self._execute(job)
            return self.job_store.mark_succeeded(project_id, job_id, result)
        except Exception as exc:
            return self.job_store.mark_failed(project_id, job_id, str(exc))

    def _execute(self, job: JobResponse) -> dict[str, Any]:
        if job.job_type == "frame_extraction":
            return self._run_frame_extraction(job)
        if job.job_type == "reconstruction_spike":
            return self._run_reconstruction_spike(job)
        raise ValueError(f"Unsupported job type: {job.job_type}")

    def _run_frame_extraction(self, job: JobResponse) -> dict[str, Any]:
        service = FrameExtractionService(self.project_store, ffmpeg_path=self.config.ffmpeg_path)
        result = service.extract_frames(
            project_id=job.project_id,
            source_video=job.params.get("source_video"),
            stride=int(job.params.get("stride", 1)),
            max_frames=job.params.get("max_frames"),
        )
        self.job_store.append_log(job.project_id, job.id, f"extracted {result.extracted_frame_count} frames")
        return result.model_dump()

    def _run_reconstruction_spike(self, job: JobResponse) -> dict[str, Any]:
        project_dir = self.project_store.get_project_dir(job.project_id)
        frames_dir = Path(job.params.get("frames_dir") or project_dir / "frames").resolve()
        reconstruction_input = inspect_frames(frames_dir)
        report = build_report(reconstruction_input, project_dir)
        report_path = write_report(project_dir, report)
        self.job_store.append_log(job.project_id, job.id, f"wrote reconstruction spike report: {report_path}")
        return report


class WorkerPool:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="roomsplat-worker")
        self._futures: dict[str, Future[JobResponse]] = {}

    def submit(self, worker: LocalWorker, project_id: str, job_id: str) -> Future[JobResponse]:
        future = self._executor.submit(worker.run_job, project_id, job_id)
        self._futures[job_id] = future
        return future


worker_pool = WorkerPool()
