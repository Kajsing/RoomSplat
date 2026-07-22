from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.models.schemas import ArtifactType
from app.services.project_store import ProjectStore, ProjectStoreError


GEOMETRY_BUNDLE_RELATIVE_PATH = Path("metadata") / "geometry_bundle.json"
SCHEMA_VERSION = "roomsplat.geometry_bundle.v1"


class GeometryBundleError(ValueError):
    pass


class GeometryBundleVector3(BaseModel):
    x: float
    y: float
    z: float


class GeometryBundleFrameMapEntry(BaseModel):
    bundle_frame_index: int = Field(ge=0)
    source_frame_index: int = Field(ge=0)
    source_frame: str


class GeometryBundleCameraPose(BaseModel):
    frame_index: int = Field(ge=0)
    position: GeometryBundleVector3
    qvec: tuple[float, float, float, float] | None = None
    transform: list[list[float]] | None = None


class GeometryBundleIntrinsic(BaseModel):
    frame_index: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fx: float = Field(gt=0)
    fy: float = Field(gt=0)
    cx: float
    cy: float


class GeometryBundleTrajectoryPoint(BaseModel):
    frame_index: int = Field(ge=0)
    position: GeometryBundleVector3


class GeometryBundleCapabilities(BaseModel):
    depth: bool = False
    confidence: bool = False
    mask: bool = False
    pointmap: bool = False


class GeometryBundlePrimaryArtifact(BaseModel):
    relative_path: str
    artifact_type: Literal["predicted_point_cloud_ply", "mesh_glb", "unsupported"]
    role: str = "primary"
    description: str


class GeometryBundleSidecar(BaseModel):
    relative_path: str
    sidecar_type: Literal["depth", "confidence", "mask", "camera_poses", "intrinsics", "trajectory", "sampling", "metadata", "other"]
    required: bool = True
    description: str


class GeometryBundleGeneratedDataRules(BaseModel):
    local_only: bool = True
    no_auto_downloads: bool = True
    contained_under_project: bool = True
    ignored_by_git: bool = True
    notes: str


class GeometryBundleQuality(BaseModel):
    status: Literal["unknown", "debug", "inspectable", "needs_review", "failed"] = "needs_review"
    notes: str


class GeometryBundle(BaseModel):
    project_id: str
    schema_version: Literal["roomsplat.geometry_bundle.v1"]
    artifact_type: Literal["learned_geometry_bundle"] = "learned_geometry_bundle"
    mode: Literal["learned_geometry"] = "learned_geometry"
    source_adapter: str
    adapter_family: Literal["learned", "feed_forward", "external", "unknown"] = "learned"
    status: Literal["complete", "incomplete", "blocked_missing_dependencies", "failed"]
    complete: bool
    is_reconstruction: bool
    not_reconstruction: bool
    frame_count: int = Field(gt=0)
    frame_index_map: list[GeometryBundleFrameMapEntry]
    cameras: list[GeometryBundleCameraPose] = Field(default_factory=list)
    intrinsics: list[GeometryBundleIntrinsic] = Field(default_factory=list)
    trajectory: list[GeometryBundleTrajectoryPoint] = Field(default_factory=list)
    capabilities: GeometryBundleCapabilities = Field(default_factory=GeometryBundleCapabilities)
    primary_artifacts: list[GeometryBundlePrimaryArtifact] = Field(default_factory=list)
    sidecars: list[GeometryBundleSidecar] = Field(default_factory=list)
    quality: GeometryBundleQuality
    warnings: list[str] = Field(default_factory=list)
    generated_data_rules: GeometryBundleGeneratedDataRules
    generated_at: str | None = None

    @model_validator(mode="after")
    def validate_consistency(self) -> "GeometryBundle":
        if self.status == "complete" and not self.complete:
            raise ValueError("complete must be true when status is complete.")
        if self.complete and self.status != "complete":
            raise ValueError("status must be complete when complete is true.")
        if self.is_reconstruction or not self.not_reconstruction:
            raise ValueError(
                "learned geometry bundles must set is_reconstruction false and not_reconstruction true "
                "until promoted to another verified artifact type."
            )
        if len(self.frame_index_map) != self.frame_count:
            raise ValueError("frame_index_map length must match frame_count.")
        if self.complete and not self.primary_artifacts:
            raise ValueError("complete geometry bundles must declare at least one primary artifact.")
        _validate_frame_indices("camera", (camera.frame_index for camera in self.cameras), self.frame_count)
        _validate_frame_indices("intrinsic", (intrinsic.frame_index for intrinsic in self.intrinsics), self.frame_count)
        _validate_frame_indices("trajectory", (point.frame_index for point in self.trajectory), self.frame_count)
        return self


class GeometryBundleService:
    def __init__(self, project_store: ProjectStore) -> None:
        self.project_store = project_store

    def read_metadata(self, project_id: str) -> dict[str, Any]:
        project_dir = self._project_dir(project_id)
        bundle = read_validated_geometry_bundle(project_dir)
        return bundle.model_dump()

    def _project_dir(self, project_id: str) -> Path:
        try:
            return self.project_store.get_project_dir(project_id)
        except ProjectStoreError as exc:
            raise GeometryBundleError(str(exc)) from exc


def read_validated_geometry_bundle(project_dir: Path) -> GeometryBundle:
    metadata_path = (project_dir / GEOMETRY_BUNDLE_RELATIVE_PATH).resolve()
    _ensure_inside_project(metadata_path, project_dir)
    if not metadata_path.is_file():
        raise GeometryBundleError("No learned geometry bundle metadata was found.")

    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GeometryBundleError("Learned geometry bundle metadata could not be read.") from exc
    if not isinstance(payload, dict):
        raise GeometryBundleError("Learned geometry bundle metadata is invalid.")

    try:
        bundle = GeometryBundle.model_validate(payload)
    except ValueError as exc:
        raise GeometryBundleError(str(exc)) from exc

    if bundle.project_id != project_dir.name:
        raise GeometryBundleError("Learned geometry bundle project_id does not match the project folder.")
    if not bundle.complete:
        raise GeometryBundleError("Learned geometry bundle is incomplete and cannot be listed as an artifact.")

    for entry in bundle.frame_index_map:
        _resolve_declared_path(project_dir, entry.source_frame, must_exist=True)
    for artifact in bundle.primary_artifacts:
        path = _resolve_declared_path(project_dir, artifact.relative_path, must_exist=True)
        _validate_primary_artifact_extension(path, artifact.artifact_type)
    for sidecar in bundle.sidecars:
        _resolve_declared_path(project_dir, sidecar.relative_path, must_exist=sidecar.required)

    return bundle


def load_geometry_artifact_types(project_dir: Path) -> dict[Path, ArtifactType]:
    try:
        bundle = read_validated_geometry_bundle(project_dir)
    except GeometryBundleError:
        return {}

    labels: dict[Path, ArtifactType] = {
        GEOMETRY_BUNDLE_RELATIVE_PATH: "learned_geometry_bundle",
    }
    for artifact in bundle.primary_artifacts:
        labels[Path(artifact.relative_path)] = artifact.artifact_type
    return labels


def load_declared_geometry_primary_paths(project_dir: Path) -> set[Path]:
    metadata_path = (project_dir / GEOMETRY_BUNDLE_RELATIVE_PATH).resolve()
    try:
        _ensure_inside_project(metadata_path, project_dir)
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, GeometryBundleError):
        return set()
    if not isinstance(payload, dict):
        return set()
    declared_paths: set[Path] = set()
    primary_artifacts = payload.get("primary_artifacts")
    if not isinstance(primary_artifacts, list):
        return declared_paths
    for artifact in primary_artifacts:
        if not isinstance(artifact, dict) or not isinstance(artifact.get("relative_path"), str):
            continue
        candidate = Path(artifact["relative_path"])
        if candidate.is_absolute() or ".." in candidate.parts:
            continue
        declared_paths.add(candidate)
    return declared_paths


def _validate_frame_indices(label: str, frame_indices: Any, frame_count: int) -> None:
    for frame_index in frame_indices:
        if frame_index >= frame_count:
            raise ValueError(f"{label} frame_index must be less than frame_count.")


def _resolve_declared_path(project_dir: Path, relative_path: str, *, must_exist: bool) -> Path:
    candidate = Path(relative_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise GeometryBundleError("Learned geometry bundle path escaped the project directory.")
    resolved = (project_dir / candidate).resolve()
    _ensure_inside_project(resolved, project_dir)
    if must_exist and not resolved.is_file():
        raise GeometryBundleError(f"Declared learned geometry file was not found: {candidate.as_posix()}")
    return resolved


def _validate_primary_artifact_extension(path: Path, artifact_type: str) -> None:
    suffix = path.suffix.lower()
    if artifact_type == "predicted_point_cloud_ply" and suffix != ".ply":
        raise GeometryBundleError("predicted_point_cloud_ply artifacts must use .ply files.")
    if artifact_type == "mesh_glb" and suffix != ".glb":
        raise GeometryBundleError("mesh_glb artifacts must use .glb files.")


def _ensure_inside_project(path: Path, project_dir: Path) -> None:
    try:
        path.resolve().relative_to(project_dir.resolve())
    except ValueError as exc:
        raise GeometryBundleError("Learned geometry bundle path escaped the project directory.") from exc
