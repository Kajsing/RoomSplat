
from __future__ import annotations

import base64
from datetime import UTC, datetime
from pathlib import Path

from app.models.schemas import ArtifactResponse, ArtifactType
from app.services.project_store import ProjectStore, ProjectStoreError


class ArtifactServiceError(ValueError):
    pass


ARTIFACT_DIRS = ("reconstruction", "exports")
ARTIFACT_EXTENSIONS = {".ply", ".glb"}
DEBUG_REPORT = Path("metadata") / "reconstruction_spike.json"


class ArtifactService:
    def __init__(self, project_store: ProjectStore) -> None:
        self.project_store = project_store

    def list_artifacts(self, project_id: str) -> list[ArtifactResponse]:
        project_dir = self._project_dir(project_id)
        artifacts: list[ArtifactResponse] = []

        for directory_name in ARTIFACT_DIRS:
            directory = (project_dir / directory_name).resolve()
            _ensure_inside_project(directory, project_dir)
            if not directory.is_dir():
                continue
            for path in sorted(directory.iterdir()):
                if path.is_file() and path.suffix.lower() in ARTIFACT_EXTENSIONS:
                    artifacts.append(self._artifact_response(project_id, project_dir, path))

        debug_report = (project_dir / DEBUG_REPORT).resolve()
        if debug_report.is_file():
            artifacts.append(self._artifact_response(project_id, project_dir, debug_report))

        return artifacts

    def resolve_artifact_path(self, project_id: str, artifact_id: str) -> Path:
        project_dir = self._project_dir(project_id)
        relative_path = _decode_artifact_id(artifact_id)
        path = (project_dir / relative_path).resolve()
        _ensure_inside_project(path, project_dir)

        allowed_paths = {Path(artifact.relative_path) for artifact in self.list_artifacts(project_id)}
        if relative_path not in allowed_paths or not path.is_file():
            raise ArtifactServiceError("Artifact was not found.")
        return path

    def _artifact_response(self, project_id: str, project_dir: Path, path: Path) -> ArtifactResponse:
        relative_path = path.relative_to(project_dir)
        artifact_type = _artifact_type(relative_path)
        artifact_id = _encode_artifact_id(relative_path)
        stat = path.stat()
        return ArtifactResponse(
            id=artifact_id,
            project_id=project_id,
            name=path.name,
            relative_path=relative_path.as_posix(),
            artifact_type=artifact_type,
            viewer_supported=artifact_type in {"point_cloud_ply", "splat_ply", "mesh_glb", "debug_report"},
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            download_url=f"/projects/{project_id}/artifacts/{artifact_id}/download",
            description=_description(artifact_type),
        )

    def _project_dir(self, project_id: str) -> Path:
        try:
            return self.project_store.get_project_dir(project_id)
        except ProjectStoreError as exc:
            raise ArtifactServiceError(str(exc)) from exc


def _artifact_type(relative_path: Path) -> ArtifactType:
    name = relative_path.name.lower()
    parent = relative_path.parent.as_posix().lower()
    if relative_path == DEBUG_REPORT:
        return "debug_report"
    if name.endswith(".glb"):
        return "mesh_glb"
    if name == "splat.ply" or "splat" in name:
        return "splat_ply"
    if name == "pointcloud.ply" or name.endswith(".ply"):
        return "point_cloud_ply"
    return "unsupported"


def _description(artifact_type: ArtifactType) -> str:
    descriptions = {
        "point_cloud_ply": "Conventional point-cloud PLY. This is not Gaussian splat data unless explicitly labeled as splat_ply.",
        "splat_ply": "Gaussian splat PLY-like artifact. This is not a conventional point cloud.",
        "mesh_glb": "Portable GLB scene or mesh artifact. Browser rendering requires GLB viewer support.",
        "debug_report": "Reconstruction spike/debug report. This is not a reconstructed 3D artifact.",
        "unsupported": "Unsupported artifact type.",
    }
    return descriptions[artifact_type]


def _encode_artifact_id(relative_path: Path) -> str:
    raw = relative_path.as_posix().encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _decode_artifact_id(artifact_id: str) -> Path:
    try:
        padding = "=" * (-len(artifact_id) % 4)
        decoded = base64.urlsafe_b64decode((artifact_id + padding).encode("ascii")).decode("utf-8")
    except Exception as exc:
        raise ArtifactServiceError("Artifact id is invalid.") from exc

    relative_path = Path(decoded)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ArtifactServiceError("Artifact id is invalid.")
    return relative_path


def _ensure_inside_project(path: Path, project_dir: Path) -> None:
    try:
        path.resolve().relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ArtifactServiceError("Artifact path escaped the project directory.") from exc
