from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.geometry_bundle import (
    GEOMETRY_BUNDLE_RELATIVE_PATH,
    SCHEMA_VERSION,
    read_validated_geometry_bundle,
)
from app.services.project_store import ProjectStore
from pipeline.adapters.learned_geometry_import import (
    DEFAULT_PRIMARY_PLY,
    LearnedGeometryImportError,
    LearnedGeometrySourceSummary,
    inspect_learned_geometry_output,
    learned_geometry_import_assessment,
)


FRAME_METADATA_RELATIVE_PATH = Path("metadata") / "frame_extraction.json"
LEARNED_PRIMARY_RELATIVE_PATH = Path("reconstruction") / "learned-point-cloud.ply"
LEARNED_SIDECAR_ROOT = Path("metadata") / "learned"
SUPPORTED_FRAME_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class LearnedGeometryImportService:
    def __init__(self, project_store: ProjectStore) -> None:
        self.project_store = project_store

    def preflight(
        self,
        project_id: str,
        *,
        source_dir: Any,
        source_adapter: Any = "local-learned-geometry",
        primary_ply: Any = DEFAULT_PRIMARY_PLY,
    ) -> dict[str, Any]:
        context = self._build_context(project_id, source_dir=source_dir, source_adapter=source_adapter, primary_ply=primary_ply)
        assessment = learned_geometry_import_assessment()
        return {
            "project_id": project_id,
            "status": "ready",
            "job_type": "learned_geometry_preflight",
            "source_adapter": context["source_adapter"],
            "adapter_family": "feed_forward",
            "source_dir": str(context["summary"].source_dir),
            "primary_ply": context["summary"].primary_ply.name,
            "frame_count": len(context["frame_index_map"]),
            "capabilities": context["summary"].capabilities,
            "sidecar_count": len(context["summary"].sidecars),
            "frame_keys": context["summary"].frame_keys,
            "global_keys": context["summary"].global_keys,
            "expected_outputs": [
                {
                    "name": artifact.name,
                    "path": artifact.path.as_posix(),
                    "artifact_type": artifact.artifact_type,
                    "description": artifact.description,
                }
                for artifact in assessment.expected_outputs
            ],
            "warnings": _base_warnings(context["summary"]),
            "generated_data_rules": _generated_data_rules(),
        }

    def import_output(
        self,
        project_id: str,
        *,
        source_dir: Any,
        source_adapter: Any = "local-learned-geometry",
        primary_ply: Any = DEFAULT_PRIMARY_PLY,
    ) -> dict[str, Any]:
        context = self._build_context(project_id, source_dir=source_dir, source_adapter=source_adapter, primary_ply=primary_ply)
        project_dir: Path = context["project_dir"]
        summary: LearnedGeometrySourceSummary = context["summary"]
        source_adapter_name: str = context["source_adapter"]
        adapter_slug = _adapter_slug(source_adapter_name)

        output_path = (project_dir / LEARNED_PRIMARY_RELATIVE_PATH).resolve()
        metadata_path = (project_dir / GEOMETRY_BUNDLE_RELATIVE_PATH).resolve()
        sidecar_root = (project_dir / LEARNED_SIDECAR_ROOT / adapter_slug).resolve()
        _ensure_inside_project(output_path, project_dir)
        _ensure_inside_project(metadata_path, project_dir)
        _ensure_inside_project(sidecar_root, project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sidecar_root.mkdir(parents=True, exist_ok=True)

        shutil.copyfile(summary.primary_ply, output_path)
        sidecars = _copy_sidecars(project_dir, sidecar_root, summary)
        metadata = {
            "project_id": project_id,
            "schema_version": SCHEMA_VERSION,
            "artifact_type": "learned_geometry_bundle",
            "mode": "learned_geometry",
            "source_adapter": source_adapter_name,
            "adapter_family": "feed_forward",
            "status": "complete",
            "complete": True,
            "is_reconstruction": False,
            "not_reconstruction": True,
            "frame_count": len(context["frame_index_map"]),
            "frame_index_map": context["frame_index_map"],
            "cameras": _read_trajectory(summary, len(context["frame_index_map"])),
            "intrinsics": _read_intrinsics(summary, len(context["frame_index_map"])),
            "trajectory": _read_trajectory_points(summary, len(context["frame_index_map"])),
            "capabilities": summary.capabilities,
            "primary_artifacts": [
                {
                    "relative_path": LEARNED_PRIMARY_RELATIVE_PATH.as_posix(),
                    "artifact_type": "predicted_point_cloud_ply",
                    "role": "primary",
                    "description": "Predicted point cloud imported from a completed local learned geometry output folder.",
                }
            ],
            "sidecars": sidecars,
            "quality": {
                "status": "needs_review",
                "notes": "Imported learned/predicted geometry. Inspect visually before treating it as useful reconstruction evidence.",
            },
            "warnings": _base_warnings(summary),
            "generated_data_rules": _generated_data_rules(),
            "generated_at": datetime.now(UTC).isoformat(),
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return read_validated_geometry_bundle(project_dir).model_dump()

    def _build_context(self, project_id: str, *, source_dir: Any, source_adapter: Any, primary_ply: Any) -> dict[str, Any]:
        if not source_dir:
            raise ValueError("source_dir is required for learned geometry import.")
        source_adapter_name = _read_source_adapter(source_adapter)
        project_dir = self.project_store.get_project_dir(project_id)
        frame_metadata = _read_frame_metadata(project_dir)
        frames_dir = _resolve_inside_project(project_dir, frame_metadata.get("frames_dir") or "frames")
        frame_paths = _list_frame_paths(frames_dir)
        if not frame_paths:
            raise ValueError("No extracted frame images were found. Extract frames before importing learned geometry.")

        try:
            summary = inspect_learned_geometry_output(source_dir, primary_ply or DEFAULT_PRIMARY_PLY)
        except LearnedGeometryImportError as exc:
            raise ValueError(str(exc)) from exc

        frame_indices = summary.frame_index_map if summary.frame_index_map is not None else list(range(len(frame_paths)))
        if not frame_indices:
            raise ValueError("Learned geometry output did not declare any frames to map.")
        frame_index_map = _build_frame_index_map(project_dir, frame_paths, frame_indices)
        return {
            "project_dir": project_dir,
            "summary": summary,
            "source_adapter": source_adapter_name,
            "frame_index_map": frame_index_map,
        }


def _build_frame_index_map(project_dir: Path, frame_paths: list[Path], frame_indices: list[int]) -> list[dict[str, Any]]:
    entries = []
    for bundle_index, source_frame_index in enumerate(frame_indices):
        if source_frame_index >= len(frame_paths):
            raise ValueError(f"Learned geometry frame_index_map references missing extracted frame index {source_frame_index}.")
        entries.append(
            {
                "bundle_frame_index": bundle_index,
                "source_frame_index": source_frame_index,
                "source_frame": frame_paths[source_frame_index].relative_to(project_dir).as_posix(),
            }
        )
    return entries


def _copy_sidecars(project_dir: Path, sidecar_root: Path, summary: LearnedGeometrySourceSummary) -> list[dict[str, Any]]:
    sidecars: list[dict[str, Any]] = []
    for sidecar in summary.sidecars:
        source_path = (summary.source_dir / sidecar.relative_path).resolve()
        try:
            source_path.relative_to(summary.source_dir)
        except ValueError as exc:
            raise ValueError("Learned geometry source path escaped source_dir.") from exc
        if not source_path.is_file():
            raise ValueError(f"Required learned geometry sidecar was not found: {sidecar.relative_path.as_posix()}")
        destination = (sidecar_root / sidecar.relative_path).resolve()
        _ensure_inside_project(destination, project_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source_path != destination:
            shutil.copyfile(source_path, destination)
        sidecars.append(
            {
                "relative_path": destination.relative_to(project_dir).as_posix(),
                "sidecar_type": sidecar.sidecar_type,
                "required": sidecar.required,
                "description": sidecar.description,
            }
        )
    return sidecars


def _read_trajectory(summary: LearnedGeometrySourceSummary, frame_count: int) -> list[dict[str, Any]]:
    traj_path = summary.source_dir / "traj.txt"
    if not traj_path.is_file():
        return []
    cameras = []
    for frame_index, transform in _read_bss_trajectory(traj_path).items():
        if frame_index >= frame_count:
            continue
        cameras.append(
            {
                "frame_index": frame_index,
                "position": {"x": transform[0][3], "y": transform[1][3], "z": transform[2][3]},
                "transform": transform,
            }
        )
    return cameras


def _read_trajectory_points(summary: LearnedGeometrySourceSummary, frame_count: int) -> list[dict[str, Any]]:
    return [
        {"frame_index": camera["frame_index"], "position": camera["position"]}
        for camera in _read_trajectory(summary, frame_count)
    ]


def _read_intrinsics(summary: LearnedGeometrySourceSummary, frame_count: int) -> list[dict[str, Any]]:
    intrinsics_path = summary.source_dir / "intrinsics.txt"
    if not intrinsics_path.is_file():
        return []
    intrinsics = []
    for line in intrinsics_path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            continue
        parts = clean_line.split()
        if len(parts) != 7:
            raise ValueError("Learned geometry intrinsics.txt contains an invalid row.")
        frame_index = int(parts[0])
        if frame_index >= frame_count or parts[1].lower() == "nan":
            continue
        intrinsics.append(
            {
                "frame_index": frame_index,
                "fx": float(parts[1]),
                "fy": float(parts[2]),
                "cx": float(parts[3]),
                "cy": float(parts[4]),
                "width": int(parts[5]),
                "height": int(parts[6]),
            }
        )
    return intrinsics


def _read_bss_trajectory(path: Path) -> dict[int, list[list[float]]]:
    transforms: dict[int, list[list[float]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            continue
        parts = clean_line.split()
        if len(parts) != 13:
            raise ValueError("Learned geometry traj.txt contains an invalid row.")
        frame_index = int(parts[0])
        if parts[1].lower() == "nan":
            continue
        values = [float(value) for value in parts[1:]]
        transforms[frame_index] = [
            values[0:4],
            values[4:8],
            values[8:12],
            [0.0, 0.0, 0.0, 1.0],
        ]
    return transforms


def _base_warnings(summary: LearnedGeometrySourceSummary) -> list[str]:
    return [
        "Imported learned/predicted geometry is not Gaussian splat data, a COLMAP sparse point cloud, or a verified metric scan.",
        "No model checkpoint was loaded by RoomSplat; this import only normalizes files already present on disk.",
        *summary.warnings,
    ]


def _generated_data_rules() -> dict[str, Any]:
    return {
        "local_only": True,
        "no_auto_downloads": True,
        "contained_under_project": True,
        "ignored_by_git": True,
        "notes": "Imported learned geometry files are copied into the local project data folder and must stay out of Git.",
    }


def _read_frame_metadata(project_dir: Path) -> dict[str, Any]:
    metadata_path = (project_dir / FRAME_METADATA_RELATIVE_PATH).resolve()
    _ensure_inside_project(metadata_path, project_dir)
    if not metadata_path.is_file():
        raise ValueError("No extracted frames metadata was found. Extract frames before importing learned geometry.")
    try:
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Frame extraction metadata could not be read.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Frame extraction metadata is invalid.")
    return payload


def _list_frame_paths(frames_dir: Path) -> list[Path]:
    if not frames_dir.is_dir():
        raise ValueError("Extracted frames directory was not found. Extract frames before importing learned geometry.")
    return sorted(path for path in frames_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_FRAME_EXTENSIONS)


def _read_source_adapter(value: Any) -> str:
    name = " ".join(str(value or "local-learned-geometry").strip().split())
    if not name:
        raise ValueError("source_adapter is required for learned geometry import.")
    if len(name) > 80:
        raise ValueError("source_adapter must be 80 characters or fewer.")
    return name


def _adapter_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", value.strip().lower()).strip("-._")
    return slug[:80] or "local-learned-geometry"


def _resolve_inside_project(project_dir: Path, requested_path: Any) -> Path:
    candidate = Path(str(requested_path))
    if not candidate.is_absolute():
        candidate = project_dir / candidate
    resolved = candidate.resolve()
    _ensure_inside_project(resolved, project_dir)
    return resolved


def _ensure_inside_project(path: Path, project_dir: Path) -> None:
    try:
        path.resolve().relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ValueError("Learned geometry import path escaped the project directory.") from exc
