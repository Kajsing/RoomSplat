
from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.models.schemas import ProjectResponse


PROJECT_SUBDIRECTORIES = ("input", "frames", "reconstruction", "exports", "metadata")


class ProjectStoreError(ValueError):
    pass


class ProjectStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir.resolve()

    def create_project(self, name: str) -> ProjectResponse:
        clean_name = _validate_project_name(name)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        project_id = uuid4().hex
        project_dir = self._safe_project_dir(project_id)
        project_dir.mkdir()

        for subdirectory in PROJECT_SUBDIRECTORIES:
            (project_dir / subdirectory).mkdir()

        created_at = datetime.now(UTC).isoformat()
        project = ProjectResponse(
            id=project_id,
            name=clean_name,
            created_at=created_at,
            path=str(project_dir),
        )
        self._write_metadata(project_dir, project)
        return project

    def list_projects(self) -> list[ProjectResponse]:
        if not self.data_dir.exists():
            return []

        projects: list[ProjectResponse] = []
        for metadata_path in self.data_dir.glob("*/metadata/project.json"):
            project = self._read_metadata(metadata_path)
            if project is not None:
                projects.append(project)

        return sorted(projects, key=lambda project: project.created_at, reverse=True)

    def _safe_project_dir(self, project_id: str) -> Path:
        if not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise ProjectStoreError("Project id is invalid.")

        project_dir = (self.data_dir / project_id).resolve()
        if not _is_relative_to(project_dir, self.data_dir):
            raise ProjectStoreError("Project path escaped the configured data directory.")
        return project_dir

    def _write_metadata(self, project_dir: Path, project: ProjectResponse) -> None:
        metadata_path = (project_dir / "metadata" / "project.json").resolve()
        if not _is_relative_to(metadata_path, self.data_dir):
            raise ProjectStoreError("Project metadata path escaped the configured data directory.")

        metadata_path.write_text(
            json.dumps(project.model_dump(), indent=2) + "\n",
            encoding="utf-8",
        )

    def _read_metadata(self, metadata_path: Path) -> ProjectResponse | None:
        resolved_path = metadata_path.resolve()
        if not _is_relative_to(resolved_path, self.data_dir):
            return None

        try:
            data = json.loads(resolved_path.read_text(encoding="utf-8"))
            return ProjectResponse.model_validate(data)
        except (OSError, json.JSONDecodeError, ValueError):
            return None


def _validate_project_name(name: str) -> str:
    clean_name = " ".join(name.strip().split())
    if not clean_name:
        raise ProjectStoreError("Project name is required.")
    if len(clean_name) > 120:
        raise ProjectStoreError("Project name must be 120 characters or fewer.")
    return clean_name


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
