from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": "local-3d-room-mapper",
        "version": "0.1.0",
    }
