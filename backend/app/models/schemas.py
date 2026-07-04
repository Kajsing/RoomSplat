from pydantic import BaseModel


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
