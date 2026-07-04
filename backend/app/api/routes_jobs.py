from fastapi import APIRouter, HTTPException

from app.config import get_config
from app.models.schemas import JobCreateRequest, JobListResponse, JobResponse
from app.services.job_store import JobStore, JobStoreError
from app.services.project_store import ProjectStore
from app.workers.local_worker import LocalWorker, worker_pool

router = APIRouter(prefix="/projects/{project_id}/jobs", tags=["jobs"])


def get_project_store() -> ProjectStore:
    return ProjectStore(get_config().data_dir)


def get_job_store() -> JobStore:
    return JobStore(get_project_store())


@router.post("", response_model=JobResponse, status_code=201)
def create_job(project_id: str, request: JobCreateRequest) -> JobResponse:
    config = get_config()
    project_store = ProjectStore(config.data_dir)
    job_store = JobStore(project_store)
    try:
        job = job_store.create_job(project_id, request.job_type, request.params)
    except JobStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    worker = LocalWorker(project_store, job_store, config)
    worker_pool.submit(worker, project_id, job.id)
    return job


@router.get("", response_model=JobListResponse)
def list_jobs(project_id: str) -> JobListResponse:
    try:
        return JobListResponse(jobs=get_job_store().list_jobs(project_id))
    except JobStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{job_id}", response_model=JobResponse)
def get_job(project_id: str, job_id: str) -> JobResponse:
    try:
        return get_job_store().get_job(project_id, job_id)
    except JobStoreError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
