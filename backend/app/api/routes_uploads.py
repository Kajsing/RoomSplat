from fastapi import APIRouter, HTTPException, Query, Request

from app.config import get_config
from app.models.schemas import FrameExtractionRequest, FrameExtractionResponse, VideoImportResponse
from app.services.frame_extraction import FrameExtractionError, FrameExtractionService
from app.services.project_store import ProjectStore
from app.services.video_import import VideoImportError, VideoImportService

router = APIRouter(prefix="/projects/{project_id}", tags=["video import"])


def get_project_store() -> ProjectStore:
    return ProjectStore(get_config().data_dir)


@router.post("/videos/upload", response_model=VideoImportResponse, status_code=201)
async def upload_video(
    project_id: str,
    request: Request,
    filename: str = Query(..., min_length=1),
) -> VideoImportResponse:
    service = VideoImportService(get_project_store())
    try:
        return service.import_uploaded_video(
            project_id=project_id,
            filename=filename,
            content=await request.body(),
            content_type=request.headers.get("content-type"),
        )
    except VideoImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/frames/extract", response_model=FrameExtractionResponse)
def extract_frames(project_id: str, request: FrameExtractionRequest) -> FrameExtractionResponse:
    config = get_config()
    service = FrameExtractionService(ProjectStore(config.data_dir), ffmpeg_path=config.ffmpeg_path)
    try:
        return service.extract_frames(
            project_id=project_id,
            source_video=request.source_video,
            stride=request.stride,
            max_frames=request.max_frames,
        )
    except FrameExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
