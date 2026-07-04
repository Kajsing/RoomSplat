from fastapi import FastAPI

from app.api.routes_health import router as health_router
from app.api.routes_projects import router as projects_router

app = FastAPI(title="local-3d-room-mapper", version="0.1.0")
app.include_router(health_router)
app.include_router(projects_router)
