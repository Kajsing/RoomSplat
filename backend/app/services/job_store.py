
from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.models.schemas import JobResponse, JobStatus, JobType
from app.services.project_store import ProjectStore, ProjectStoreError


class JobStoreError(ValueError):
    pass


class JobStore:
    def __init__(self, project_store: ProjectStore) -> None:
        self.project_store = project_store

    def create_job(self, project_id: str, job_type: JobType, params: dict) -> JobResponse:
        project_dir = self._project_dir(project_id)
        jobs_dir = self._jobs_dir(project_dir)
        job_id = uuid4().hex
        now = _now()
        log_path = jobs_dir / f"{job_id}.log"
        job = JobResponse(
            id=job_id,
            project_id=project_id,
            job_type=job_type,
            status="queued",
            params=params,
            created_at=now,
            updated_at=now,
            log_path=str(log_path),
        )
        self._write_job(project_dir, job)
        self.append_log(project_id, job_id, "queued")
        return job

    def get_job(self, project_id: str, job_id: str) -> JobResponse:
        project_dir = self._project_dir(project_id)
        job_path = self._job_path(project_dir, job_id)
        if not job_path.is_file():
            raise JobStoreError("Job was not found.")
        try:
            return JobResponse.model_validate(json.loads(job_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise JobStoreError("Job metadata could not be read.") from exc

    def list_jobs(self, project_id: str) -> list[JobResponse]:
        project_dir = self._project_dir(project_id)
        jobs_dir = self._jobs_dir(project_dir)
        jobs: list[JobResponse] = []
        for job_path in jobs_dir.glob("*.json"):
            try:
                jobs.append(JobResponse.model_validate(json.loads(job_path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError, ValueError):
                continue
        return sorted(jobs, key=lambda job: job.created_at, reverse=True)

    def mark_running(self, project_id: str, job_id: str) -> JobResponse:
        job = self.get_job(project_id, job_id)
        now = _now()
        updated = job.model_copy(update={"status": "running", "started_at": job.started_at or now, "updated_at": now})
        self._write_job(self._project_dir(project_id), updated)
        self.append_log(project_id, job_id, "running")
        return updated

    def mark_succeeded(self, project_id: str, job_id: str, result: dict) -> JobResponse:
        job = self.get_job(project_id, job_id)
        now = _now()
        updated = job.model_copy(update={"status": "succeeded", "result": result, "finished_at": now, "updated_at": now})
        self._write_job(self._project_dir(project_id), updated)
        self.append_log(project_id, job_id, "succeeded")
        return updated

    def mark_failed(self, project_id: str, job_id: str, error: str) -> JobResponse:
        job = self.get_job(project_id, job_id)
        now = _now()
        updated = job.model_copy(update={"status": "failed", "error": error, "finished_at": now, "updated_at": now})
        self._write_job(self._project_dir(project_id), updated)
        self.append_log(project_id, job_id, f"failed: {error}")
        return updated

    def append_log(self, project_id: str, job_id: str, message: str) -> None:
        project_dir = self._project_dir(project_id)
        log_path = self._log_path(project_dir, job_id)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"{_now()} {message}\n")

    def _project_dir(self, project_id: str) -> Path:
        try:
            return self.project_store.get_project_dir(project_id)
        except ProjectStoreError as exc:
            raise JobStoreError(str(exc)) from exc

    def _jobs_dir(self, project_dir: Path) -> Path:
        jobs_dir = (project_dir / "metadata" / "jobs").resolve()
        _ensure_inside_project(jobs_dir, project_dir)
        jobs_dir.mkdir(parents=True, exist_ok=True)
        return jobs_dir

    def _job_path(self, project_dir: Path, job_id: str) -> Path:
        if not job_id or "/" in job_id or "\\" in job_id:
            raise JobStoreError("Job id is invalid.")
        job_path = (self._jobs_dir(project_dir) / f"{job_id}.json").resolve()
        _ensure_inside_project(job_path, project_dir)
        return job_path

    def _log_path(self, project_dir: Path, job_id: str) -> Path:
        if not job_id or "/" in job_id or "\\" in job_id:
            raise JobStoreError("Job id is invalid.")
        log_path = (self._jobs_dir(project_dir) / f"{job_id}.log").resolve()
        _ensure_inside_project(log_path, project_dir)
        return log_path

    def _write_job(self, project_dir: Path, job: JobResponse) -> None:
        job_path = self._job_path(project_dir, job.id)
        job_path.write_text(json.dumps(job.model_dump(), indent=2) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _ensure_inside_project(path: Path, project_dir: Path) -> None:
    try:
        path.resolve().relative_to(project_dir.resolve())
    except ValueError as exc:
        raise JobStoreError("Job path escaped the project directory.") from exc
