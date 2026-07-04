from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_config
from app.models.schemas import ArtifactListResponse
from app.services.export_service import ArtifactService, ArtifactServiceError
from app.services.project_store import ProjectStore

router = APIRouter(prefix="/projects/{project_id}/artifacts", tags=["artifacts"])


def get_artifact_service() -> ArtifactService:
    return ArtifactService(ProjectStore(get_config().data_dir))


@router.get("", response_model=ArtifactListResponse)
def list_artifacts(project_id: str) -> ArtifactListResponse:
    try:
        return ArtifactListResponse(artifacts=get_artifact_service().list_artifacts(project_id))
    except ArtifactServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{artifact_id}/download")
def download_artifact(project_id: str, artifact_id: str) -> FileResponse:
    try:
        artifact_path = get_artifact_service().resolve_artifact_path(project_id, artifact_id)
    except ArtifactServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(artifact_path, filename=artifact_path.name)
