from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_config
from app.models.schemas import ArtifactListResponse, ExportCreateRequest, ExportListResponse, ExportResponse
from app.services.debug_frame_cloud import DebugFrameCloudService
from app.services.export_service import ArtifactService, ArtifactServiceError, ExportService
from app.services.geometry_bundle import GeometryBundleError, GeometryBundleService
from app.services.project_store import ProjectStore
from app.services.reconstruction_jobs import ReconstructionService

router = APIRouter(tags=["artifacts", "exports"])


def get_artifact_service() -> ArtifactService:
    return ArtifactService(ProjectStore(get_config().data_dir))


def get_export_service() -> ExportService:
    return ExportService(get_artifact_service())


def get_debug_frame_cloud_service() -> DebugFrameCloudService:
    return DebugFrameCloudService(ProjectStore(get_config().data_dir))


def get_reconstruction_service() -> ReconstructionService:
    config = get_config()
    return ReconstructionService(ProjectStore(config.data_dir), colmap_path=config.colmap_path)


def get_geometry_bundle_service() -> GeometryBundleService:
    return GeometryBundleService(ProjectStore(get_config().data_dir))


@router.get("/projects/{project_id}/artifacts", response_model=ArtifactListResponse)
def list_artifacts(project_id: str) -> ArtifactListResponse:
    try:
        return ArtifactListResponse(artifacts=get_artifact_service().list_artifacts(project_id))
    except ArtifactServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/artifacts/{artifact_id}/download")
def download_artifact(project_id: str, artifact_id: str) -> FileResponse:
    try:
        artifact_path = get_artifact_service().resolve_artifact_path(project_id, artifact_id)
    except ArtifactServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(artifact_path, filename=artifact_path.name)


@router.get("/projects/{project_id}/debug-frame-cloud")
def get_debug_frame_cloud_metadata(project_id: str) -> dict:
    try:
        return get_debug_frame_cloud_service().read_metadata(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/reconstruction")
def get_reconstruction_metadata(project_id: str) -> dict:
    try:
        return get_reconstruction_service().read_metadata(project_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/projects/{project_id}/geometry-bundle")
def get_geometry_bundle_metadata(project_id: str) -> dict:
    try:
        return get_geometry_bundle_service().read_metadata(project_id)
    except GeometryBundleError as exc:
        status_code = 404 if "No learned geometry bundle metadata" in str(exc) else 400
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/projects/{project_id}/exports", response_model=ExportResponse, status_code=201)
def create_export(project_id: str, request: ExportCreateRequest) -> ExportResponse:
    try:
        return get_export_service().create_export(
            project_id,
            source_artifact_id=request.source_artifact_id,
            export_format=request.format,
            allow_placeholder=request.allow_placeholder,
        )
    except ArtifactServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/projects/{project_id}/exports", response_model=ExportListResponse)
def list_exports(project_id: str) -> ExportListResponse:
    try:
        return ExportListResponse(exports=get_export_service().list_exports(project_id))
    except ArtifactServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
