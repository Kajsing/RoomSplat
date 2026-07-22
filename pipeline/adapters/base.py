from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

GEOMETRY_BUNDLE_SCHEMA_VERSION = "roomsplat.geometry_bundle.v1"
LEARNED_GEOMETRY_BUNDLE_ARTIFACT_TYPE = "learned_geometry_bundle"
PREDICTED_POINT_CLOUD_ARTIFACT_TYPE = "predicted_point_cloud_ply"
GEOMETRY_BUNDLE_RELATIVE_PATH = Path("metadata") / "geometry_bundle.json"


@dataclass(frozen=True)
class DependencyCheck:
    name: str
    available: bool
    kind: str
    detail: str


@dataclass(frozen=True)
class ReconstructionInput:
    frames_dir: Path
    frame_count: int
    width: int
    height: int


@dataclass(frozen=True)
class ReconstructionArtifact:
    name: str
    path: Path
    artifact_type: str
    description: str


@dataclass(frozen=True)
class AdapterAssessment:
    adapter: str
    status: str
    summary: str
    dependencies: list[DependencyCheck] = field(default_factory=list)
    expected_outputs: list[ReconstructionArtifact] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"


class ReconstructionAdapter(Protocol):
    name: str
    description: str

    def assess(self, reconstruction_input: ReconstructionInput) -> AdapterAssessment:
        pass


def python_module_dependency(module_name: str, package_name: str | None = None) -> DependencyCheck:
    label = package_name or module_name
    available = importlib.util.find_spec(module_name) is not None
    return DependencyCheck(
        name=label,
        available=available,
        kind="python_module",
        detail="installed" if available else f"Install with pip if this adapter is selected: {label}",
    )


def executable_dependency(executable_name: str) -> DependencyCheck:
    path = shutil.which(executable_name)
    return DependencyCheck(
        name=executable_name,
        available=path is not None,
        kind="executable",
        detail=path or f"Add {executable_name} to PATH if this adapter is selected.",
    )


def dependencies_available(dependencies: list[DependencyCheck]) -> bool:
    return all(dependency.available for dependency in dependencies)


def learned_geometry_expected_outputs(primary_name: str = "learned-point-cloud.ply") -> list[ReconstructionArtifact]:
    return [
        ReconstructionArtifact(
            name="Geometry bundle manifest",
            path=GEOMETRY_BUNDLE_RELATIVE_PATH,
            artifact_type=LEARNED_GEOMETRY_BUNDLE_ARTIFACT_TYPE,
            description=(
                "RoomSplat learned-geometry manifest with frame mapping, camera metadata, "
                "sidecar declarations, generated-data rules, and quality notes."
            ),
        ),
        ReconstructionArtifact(
            name="Predicted point cloud",
            path=Path("reconstruction") / primary_name,
            artifact_type=PREDICTED_POINT_CLOUD_ARTIFACT_TYPE,
            description=(
                "Learned/predicted point-cloud PLY declared by a geometry bundle. "
                "This is not Gaussian splat data or a verified metric reconstruction."
            ),
        ),
    ]


def validate_geometry_expected_outputs(artifacts: list[ReconstructionArtifact]) -> None:
    artifact_by_type = {artifact.artifact_type: artifact for artifact in artifacts}
    bundle = artifact_by_type.get(LEARNED_GEOMETRY_BUNDLE_ARTIFACT_TYPE)
    predicted = artifact_by_type.get(PREDICTED_POINT_CLOUD_ARTIFACT_TYPE)

    if bundle is None:
        raise ValueError("Learned geometry adapters must declare metadata/geometry_bundle.json.")
    if bundle.path != GEOMETRY_BUNDLE_RELATIVE_PATH:
        raise ValueError("Learned geometry bundle manifests must be written to metadata/geometry_bundle.json.")
    if predicted is None:
        raise ValueError("Learned geometry adapters must declare a predicted_point_cloud_ply primary artifact.")
    if predicted.path.suffix.lower() != ".ply":
        raise ValueError("predicted_point_cloud_ply artifacts must use a .ply file.")

    for artifact in artifacts:
        if artifact.path.is_absolute() or ".." in artifact.path.parts:
            raise ValueError(f"Artifact paths must stay project-relative: {artifact.path}")
