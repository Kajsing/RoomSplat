
from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.models.schemas import VideoImportResponse
from app.services.project_store import ProjectStore, ProjectStoreError


ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".gif"}


class VideoImportError(ValueError):
    pass


class VideoImportService:
    def __init__(self, project_store: ProjectStore) -> None:
        self.project_store = project_store

    def import_uploaded_video(
        self,
        project_id: str,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> VideoImportResponse:
        if not content:
            raise VideoImportError("Uploaded video is empty.")

        original_filename = _sanitize_filename(filename)
        suffix = Path(original_filename).suffix.lower()
        if suffix not in ALLOWED_VIDEO_EXTENSIONS:
            allowed = ", ".join(sorted(ALLOWED_VIDEO_EXTENSIONS))
            raise VideoImportError(f"Unsupported video extension. Expected one of: {allowed}.")

        try:
            project_dir = self.project_store.get_project_dir(project_id)
        except ProjectStoreError as exc:
            raise VideoImportError(str(exc)) from exc

        stored_filename = f"{Path(original_filename).stem}-{uuid4().hex[:8]}{suffix}"
        input_path = (project_dir / "input" / stored_filename).resolve()
        _ensure_inside_project(input_path, project_dir)
        input_path.write_bytes(content)

        imported_at = datetime.now(UTC).isoformat()
        response = VideoImportResponse(
            project_id=project_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            source_video=str(input_path),
            size_bytes=len(content),
            content_type=content_type,
            imported_at=imported_at,
        )
        metadata_path = (project_dir / "metadata" / "video_import.json").resolve()
        _ensure_inside_project(metadata_path, project_dir)
        metadata_path.write_text(json.dumps(response.model_dump(), indent=2) + "\n", encoding="utf-8")
        return response


def _sanitize_filename(filename: str) -> str:
    leaf_name = Path(filename or "").name.strip()
    if not leaf_name:
        raise VideoImportError("A filename is required.")

    sanitized = re.sub(r"[^A-Za-z0-9._ -]+", "_", leaf_name)
    sanitized = sanitized.strip(" .")
    if not sanitized:
        raise VideoImportError("A filename is required.")
    return sanitized[:160]


def _ensure_inside_project(path: Path, project_dir: Path) -> None:
    try:
        path.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise VideoImportError("Video path escaped the project directory.") from exc
