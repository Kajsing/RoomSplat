from typing import Any, Literal

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


JobType = Literal["frame_extraction", "reconstruction_spike"]
JobStatus = Literal["queued", "running", "succeeded", "failed"]
ArtifactType = Literal["point_cloud_ply", "splat_ply", "mesh_glb", "debug_report", "unsupported"]


class JobCreateRequest(BaseModel):
    job_type: JobType
    params: dict[str, Any] = Field(default_factory=dict)


class JobResponse(BaseModel):
    id: str
    project_id: str
    job_type: JobType
    status: JobStatus
    params: dict[str, Any]
    created_at: str
    updated_at: str
    started_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    log_path: str


class JobListResponse(BaseModel):
    jobs: list[JobResponse]


class ArtifactResponse(BaseModel):
    id: str
    project_id: str
    name: str
    relative_path: str
    artifact_type: ArtifactType
    viewer_supported: bool
    size_bytes: int
    modified_at: str
    download_url: str
    description: str


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactResponse]
