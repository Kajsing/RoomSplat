from fastapi import APIRouter, HTTPException

from app.config import get_config
from app.models.schemas import ProjectCreateRequest, ProjectListResponse, ProjectResponse
from app.services.project_store import ProjectStore, ProjectStoreError

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_store() -> ProjectStore:
    return ProjectStore(get_config().data_dir)


@router.get("", response_model=ProjectListResponse)
def list_projects() -> ProjectListResponse:
    return ProjectListResponse(projects=get_project_store().list_projects())


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(request: ProjectCreateRequest) -> ProjectResponse:
    try:
        return get_project_store().create_project(request.name)
    except ProjectStoreError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
