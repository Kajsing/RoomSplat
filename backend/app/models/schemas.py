from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str


class ProjectCreateRequest(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: str
    path: str


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


class VideoImportResponse(BaseModel):
    project_id: str
    original_filename: str
    stored_filename: str
    source_video: str
    size_bytes: int
    content_type: str | None
    imported_at: str


class FrameExtractionRequest(BaseModel):
    source_video: str | None = None
    stride: int = Field(default=1, ge=1)
    max_frames: int | None = Field(default=None, ge=1)


class FrameExtractionResponse(BaseModel):
    project_id: str
    source_video: str
    frames_dir: str
    fps: float
    frame_count: int
    extracted_frame_count: int
    extraction_stride: int
    width: int
    height: int
    extracted_at: str
