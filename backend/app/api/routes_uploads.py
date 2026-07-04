import json

from fastapi import APIRouter, HTTPException, Query, Request

from app.config import get_config
from app.models.schemas import FrameExtractionRequest, FrameExtractionResponse, VideoImportResponse
from app.services.frame_extraction import FrameExtractionError, FrameExtractionService
from app.services.project_store import ProjectStore, ProjectStoreError
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
    config = get_config()
    service = VideoImportService(get_project_store())
    try:
        return service.import_uploaded_video(
            project_id=project_id,
            filename=filename,
            content=await _read_limited_body(request, config.max_upload_bytes),
            content_type=request.headers.get("content-type"),
        )
    except VideoImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/frames/extract", response_model=FrameExtractionResponse)
def extract_frames(project_id: str, request: FrameExtractionRequest) -> FrameExtractionResponse:
    config = get_config()
    service = FrameExtractionService(
        ProjectStore(config.data_dir),
        ffmpeg_path=config.ffmpeg_path,
        ffmpeg_timeout_seconds=config.ffmpeg_timeout_seconds,
    )
    try:
        return service.extract_frames(
            project_id=project_id,
            source_video=request.source_video,
            stride=request.stride,
            max_frames=request.max_frames,
        )
    except FrameExtractionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/frames/extraction", response_model=FrameExtractionResponse)
def get_frame_extraction(project_id: str) -> FrameExtractionResponse:
    try:
        project_dir = get_project_store().get_project_dir(project_id)
    except ProjectStoreError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    metadata_path = (project_dir / "metadata" / "frame_extraction.json").resolve()
    try:
        metadata_path.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Frame extraction metadata path escaped the project directory.") from exc
    if not metadata_path.is_file():
        raise HTTPException(status_code=404, detail="No extracted frames metadata was found.")

    try:
        return FrameExtractionResponse.model_validate(json.loads(metadata_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Frame extraction metadata is invalid.") from exc


async def _read_limited_body(request: Request, max_bytes: int) -> bytes:
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise HTTPException(status_code=413, detail="Uploaded video exceeds the configured maximum size.")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Content-Length header is invalid.") from exc

    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail="Uploaded video exceeds the configured maximum size.")
        chunks.append(chunk)
    return b"".join(chunks)
