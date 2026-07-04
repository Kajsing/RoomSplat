from __future__ import annotations

import base64
import json
import shutil
import struct
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.models.schemas import ArtifactResponse, ArtifactType, ExportFormat, ExportResponse, ExportStatus
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
                if path.is_file() and path.suffix.lower() in ARTIFACT_EXTENSIONS and _is_inside_project(path, project_dir):
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
            viewer_supported=artifact_type in {"debug_frame_cloud_ply", "point_cloud_ply", "splat_ply", "mesh_glb", "debug_report"},
            size_bytes=stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            download_url=f"/projects/{project_id}/artifacts/{artifact_id}/download",
            description=_description(artifact_type, relative_path),
        )

    def _project_dir(self, project_id: str) -> Path:
        try:
            return self.project_store.get_project_dir(project_id)
        except ProjectStoreError as exc:
            raise ArtifactServiceError(str(exc)) from exc


class ExportService:
    def __init__(self, artifact_service: ArtifactService) -> None:
        self.artifact_service = artifact_service

    def create_export(
        self,
        project_id: str,
        source_artifact_id: str,
        export_format: ExportFormat,
        allow_placeholder: bool = False,
    ) -> ExportResponse:
        project_dir = self.artifact_service._project_dir(project_id)
        source_path = self.artifact_service.resolve_artifact_path(project_id, source_artifact_id)
        source_relative_path = source_path.relative_to(project_dir)
        source_type = _artifact_type(source_relative_path)
        export_id = uuid4().hex
        generated_at = datetime.now(UTC).isoformat()

        if source_type == "debug_report":
            if not allow_placeholder:
                raise ArtifactServiceError("Debug reports can only be exported as placeholders when allow_placeholder is true.")
            response = self._create_placeholder_export(
                project_id,
                project_dir,
                source_artifact_id,
                source_relative_path,
                export_id,
                export_format,
                generated_at,
            )
        else:
            if export_format != _format_for_artifact_type(source_type):
                raise ArtifactServiceError("Requested export format does not match the source artifact type.")
            response = self._copy_real_export(
                project_id,
                project_dir,
                source_artifact_id,
                source_path,
                source_relative_path,
                export_id,
                export_format,
                source_type,
                generated_at,
            )

        self._write_metadata(project_dir, response)
        return response

    def list_exports(self, project_id: str) -> list[ExportResponse]:
        project_dir = self.artifact_service._project_dir(project_id)
        metadata_dir = self._metadata_dir(project_dir)
        exports: list[ExportResponse] = []
        for path in metadata_dir.glob("*.json"):
            try:
                exports.append(ExportResponse.model_validate(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, json.JSONDecodeError, ValueError):
                continue
        return sorted(exports, key=lambda item: item.generated_at, reverse=True)

    def _copy_real_export(
        self,
        project_id: str,
        project_dir: Path,
        source_artifact_id: str,
        source_path: Path,
        source_relative_path: Path,
        export_id: str,
        export_format: ExportFormat,
        artifact_type: ArtifactType,
        generated_at: str,
    ) -> ExportResponse:
        export_path = (project_dir / "exports" / f"{source_path.stem}-{export_id[:8]}.{export_format}").resolve()
        _ensure_inside_project(export_path, project_dir)
        export_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, export_path)
        return self._response(
            project_id,
            project_dir,
            source_artifact_id,
            source_relative_path,
            export_path,
            export_format,
            artifact_type,
            "real",
            generated_at,
            warning=None,
        )

    def _create_placeholder_export(
        self,
        project_id: str,
        project_dir: Path,
        source_artifact_id: str,
        source_relative_path: Path,
        export_id: str,
        export_format: ExportFormat,
        generated_at: str,
    ) -> ExportResponse:
        stem = f"placeholder-reconstruction-spike-{export_id[:8]}"
        export_path = (project_dir / "exports" / f"{stem}.{export_format}").resolve()
        _ensure_inside_project(export_path, project_dir)
        export_path.parent.mkdir(parents=True, exist_ok=True)

        if export_format == "ply":
            export_path.write_text(_placeholder_ply(), encoding="utf-8")
            artifact_type: ArtifactType = "point_cloud_ply"
        else:
            export_path.write_bytes(_placeholder_glb())
            artifact_type = "mesh_glb"

        return self._response(
            project_id,
            project_dir,
            source_artifact_id,
            source_relative_path,
            export_path,
            export_format,
            artifact_type,
            "placeholder",
            generated_at,
            warning="Placeholder export generated from reconstruction spike debug report; not a real reconstruction.",
        )

    def _response(
        self,
        project_id: str,
        project_dir: Path,
        source_artifact_id: str,
        source_relative_path: Path,
        export_path: Path,
        export_format: ExportFormat,
        artifact_type: ArtifactType,
        status: ExportStatus,
        generated_at: str,
        warning: str | None,
    ) -> ExportResponse:
        export_relative_path = export_path.relative_to(project_dir)
        export_artifact_id = _encode_artifact_id(export_relative_path)
        metadata_path = self._metadata_dir(project_dir) / f"{export_path.stem}.json"
        return ExportResponse(
            id=export_path.stem,
            project_id=project_id,
            source_artifact_id=source_artifact_id,
            source_relative_path=source_relative_path.as_posix(),
            export_relative_path=export_relative_path.as_posix(),
            format=export_format,
            artifact_type=artifact_type,
            status=status,
            generated_at=generated_at,
            metadata_path=metadata_path.relative_to(project_dir).as_posix(),
            download_url=f"/projects/{project_id}/artifacts/{export_artifact_id}/download",
            warning=warning,
        )

    def _metadata_dir(self, project_dir: Path) -> Path:
        metadata_dir = (project_dir / "metadata" / "exports").resolve()
        _ensure_inside_project(metadata_dir, project_dir)
        metadata_dir.mkdir(parents=True, exist_ok=True)
        return metadata_dir

    def _write_metadata(self, project_dir: Path, response: ExportResponse) -> None:
        metadata_path = (project_dir / response.metadata_path).resolve()
        _ensure_inside_project(metadata_path, project_dir)
        metadata_path.write_text(json.dumps(response.model_dump(), indent=2) + "\n", encoding="utf-8")


def _artifact_type(relative_path: Path) -> ArtifactType:
    name = relative_path.name.lower()
    parent = relative_path.parent.as_posix().lower()
    if relative_path == DEBUG_REPORT:
        return "debug_report"
    if name == "debug-frame-room.ply" or name.startswith("debug-frame-"):
        return "debug_frame_cloud_ply"
    if name.endswith(".glb"):
        return "mesh_glb"
    if name == "splat.ply" or "splat" in name:
        return "splat_ply"
    if name == "pointcloud.ply" or name.endswith(".ply"):
        return "point_cloud_ply"
    return "unsupported"


def _description(artifact_type: ArtifactType, relative_path: Path | None = None) -> str:
    if relative_path and relative_path.parent.name == "exports" and relative_path.name.startswith("placeholder-"):
        return "Placeholder export for workflow/debug testing. This is not a real reconstruction."

    descriptions = {
        "debug_frame_cloud_ply": "Debug frame planes sampled from extracted frames and placed in 3D for viewer inspection. This is not a reconstruction.",
        "point_cloud_ply": "Conventional point-cloud PLY. This is not Gaussian splat data unless explicitly labeled as splat_ply.",
        "splat_ply": "Gaussian splat PLY-like artifact. This is not a conventional point cloud.",
        "mesh_glb": "Portable GLB scene or mesh artifact. Browser rendering requires GLB viewer support.",
        "debug_report": "Reconstruction spike/debug report. This is not a reconstructed 3D artifact.",
        "unsupported": "Unsupported artifact type.",
    }
    if artifact_type == "point_cloud_ply" and relative_path and relative_path.name == "sparse-point-cloud.ply":
        return "Sparse COLMAP point-cloud reconstruction. This is conventional point geometry, not Gaussian splat data."
    return descriptions[artifact_type]


def _format_for_artifact_type(artifact_type: ArtifactType) -> ExportFormat:
    if artifact_type in {"debug_frame_cloud_ply", "point_cloud_ply", "splat_ply"}:
        return "ply"
    if artifact_type == "mesh_glb":
        return "glb"
    raise ArtifactServiceError("Only PLY and GLB artifacts can be exported as real outputs.")


def _placeholder_ply() -> str:
    return "\n".join(
        [
            "ply",
            "format ascii 1.0",
            "comment RoomSplat placeholder export; not a real reconstruction.",
            "element vertex 1",
            "property float x",
            "property float y",
            "property float z",
            "property uchar red",
            "property uchar green",
            "property uchar blue",
            "end_header",
            "0 0 0 255 0 255",
            "",
        ]
    )


def _placeholder_glb() -> bytes:
    payload = json.dumps(
        {
            "asset": {"version": "2.0", "generator": "RoomSplat placeholder export"},
            "extras": {"placeholder": True, "warning": "Not a real reconstruction."},
        },
        separators=(",", ":"),
    ).encode("utf-8")
    padding = b" " * (-len(payload) % 4)
    json_chunk = payload + padding
    total_length = 12 + 8 + len(json_chunk)
    return b"glTF" + struct.pack("<II", 2, total_length) + struct.pack("<II", len(json_chunk), 0x4E4F534A) + json_chunk


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


def _is_inside_project(path: Path, project_dir: Path) -> bool:
    try:
        path.resolve().relative_to(project_dir.resolve())
        return True
    except ValueError:
        return False
