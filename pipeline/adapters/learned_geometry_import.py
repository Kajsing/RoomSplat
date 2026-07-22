from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pipeline.adapters.base import (
    AdapterAssessment,
    DependencyCheck,
    ReconstructionArtifact,
    learned_geometry_expected_outputs,
    validate_geometry_expected_outputs,
)


LEARNED_COMPLETION_FILE = ".complete.json"
DEFAULT_PRIMARY_PLY = "points.ply"
SUPPORTED_FRAME_SIDECAR_EXTENSIONS = {
    "depth": {".exr", ".npy", ".npz", ".jpg", ".jpeg", ".png"},
    "confidence": {".exr", ".npy", ".npz", ".jpg", ".jpeg", ".png"},
    "mask": {".png", ".jpg", ".jpeg", ".npy", ".npz"},
    "points": {".exr", ".npy", ".npz"},
}
FRAME_KEY_TO_SIDECAR_TYPE = {
    "depth": "depth",
    "confidence": "confidence",
    "mask": "mask",
    "points": "pointmap",
}


class LearnedGeometryImportError(ValueError):
    pass


@dataclass(frozen=True)
class LearnedGeometrySidecarCandidate:
    relative_path: Path
    sidecar_type: Literal["depth", "confidence", "mask", "pointmap", "intrinsics", "trajectory", "sampling", "metadata", "other"]
    required: bool
    description: str


@dataclass(frozen=True)
class LearnedGeometrySourceSummary:
    source_dir: Path
    primary_ply: Path
    completion_metadata_path: Path
    completion_metadata: dict[str, Any]
    frame_keys: list[str]
    global_keys: list[str]
    frame_index_map: list[int] | None
    sidecars: list[LearnedGeometrySidecarCandidate] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def frame_count(self) -> int | None:
        return len(self.frame_index_map) if self.frame_index_map is not None else None

    @property
    def capabilities(self) -> dict[str, bool]:
        return {
            "depth": "depth" in self.frame_keys,
            "confidence": "confidence" in self.frame_keys,
            "mask": "mask" in self.frame_keys,
            "pointmap": "points" in self.frame_keys,
        }


def learned_geometry_import_assessment() -> AdapterAssessment:
    expected_outputs = learned_geometry_expected_outputs()
    validate_geometry_expected_outputs(expected_outputs)
    return AdapterAssessment(
        adapter="local-learned-geometry-import",
        status="ready",
        summary="Can normalize a completed local learned-geometry output folder into a RoomSplat geometry bundle.",
        dependencies=[
            DependencyCheck(
                name="completed_output_folder",
                available=True,
                kind="local_filesystem_contract",
                detail="Requires a local folder with .complete.json and a primary PLY such as points.ply.",
            )
        ],
        expected_outputs=expected_outputs,
        next_steps=[
            "Run preflight against the local output folder.",
            "Import only after extracted project frames and required sidecars are present.",
        ],
    )


def inspect_learned_geometry_output(source_dir: str | Path, primary_ply: str | Path = DEFAULT_PRIMARY_PLY) -> LearnedGeometrySourceSummary:
    root = Path(source_dir).expanduser().resolve()
    if not root.is_dir():
        raise LearnedGeometryImportError("Learned geometry source_dir was not found or is not a directory.")

    completion_path = _resolve_inside_source(root, LEARNED_COMPLETION_FILE)
    if not completion_path.is_file():
        raise LearnedGeometryImportError("Learned geometry source_dir is incomplete: .complete.json was not found.")

    completion_payload = _read_json(completion_path, "Learned geometry completion metadata could not be read.")
    completion_metadata = completion_payload.get("metadata", completion_payload)
    if not isinstance(completion_metadata, dict):
        raise LearnedGeometryImportError("Learned geometry completion metadata is invalid.")

    primary_path = _resolve_inside_source(root, primary_ply)
    if not primary_path.is_file():
        raise LearnedGeometryImportError(f"Learned geometry primary PLY was not found: {Path(primary_ply).as_posix()}")
    if primary_path.suffix.lower() != ".ply":
        raise LearnedGeometryImportError("Learned geometry primary artifact must be a .ply file.")

    frame_keys = _read_string_list(completion_metadata.get("frame_keys"), "frame_keys")
    global_keys = _read_string_list(completion_metadata.get("global_keys"), "global_keys")
    frame_index_map = _read_frame_index_map(completion_metadata.get("frame_index_map"))
    warnings: list[str] = []
    sidecars = [
        LearnedGeometrySidecarCandidate(
            relative_path=Path(LEARNED_COMPLETION_FILE),
            sidecar_type="metadata",
            required=True,
            description="Source completion marker copied from the local learned geometry output folder.",
        )
    ]

    if "points" not in global_keys:
        warnings.append("Completion metadata does not declare global points; importing the configured primary PLY anyway.")

    if (root / "sampling.json").is_file():
        sidecars.append(
            LearnedGeometrySidecarCandidate(
                relative_path=Path("sampling.json"),
                sidecar_type="sampling",
                required=True,
                description="Sampling metadata from the learned geometry output folder.",
            )
        )

    if "pose" in frame_keys or (root / "traj.txt").is_file():
        _require_file(root, "traj.txt", "Completion metadata declares pose output, but traj.txt was not found.")
        sidecars.append(
            LearnedGeometrySidecarCandidate(
                relative_path=Path("traj.txt"),
                sidecar_type="trajectory",
                required=True,
                description="Camera-to-world trajectory from the learned geometry output folder.",
            )
        )

    if "intrinsics" in frame_keys or (root / "intrinsics.txt").is_file():
        _require_file(root, "intrinsics.txt", "Completion metadata declares intrinsics output, but intrinsics.txt was not found.")
        sidecars.append(
            LearnedGeometrySidecarCandidate(
                relative_path=Path("intrinsics.txt"),
                sidecar_type="intrinsics",
                required=True,
                description="Per-frame camera intrinsics from the learned geometry output folder.",
            )
        )

    for frame_key, sidecar_type in FRAME_KEY_TO_SIDECAR_TYPE.items():
        if frame_key not in frame_keys:
            continue
        sidecar_files = _list_frame_sidecar_files(root, frame_key)
        if not sidecar_files:
            raise LearnedGeometryImportError(f"Completion metadata declares {frame_key} output, but no supported files were found in {frame_key}/.")
        sidecars.extend(
            LearnedGeometrySidecarCandidate(
                relative_path=path.relative_to(root),
                sidecar_type=sidecar_type,
                required=True,
                description=f"Per-frame {frame_key} sidecar from the learned geometry output folder.",
            )
            for path in sidecar_files
        )

    return LearnedGeometrySourceSummary(
        source_dir=root,
        primary_ply=primary_path,
        completion_metadata_path=completion_path,
        completion_metadata=completion_metadata,
        frame_keys=frame_keys,
        global_keys=global_keys,
        frame_index_map=frame_index_map,
        sidecars=sidecars,
        warnings=warnings,
    )


def learned_geometry_expected_sidecars(frame_keys: list[str]) -> list[str]:
    expected = [LEARNED_COMPLETION_FILE]
    if "pose" in frame_keys:
        expected.append("traj.txt")
    if "intrinsics" in frame_keys:
        expected.append("intrinsics.txt")
    expected.extend(f"{key}/" for key in ("depth", "confidence", "mask", "points") if key in frame_keys)
    return expected


def learned_geometry_expected_artifacts(primary_name: str = "learned-point-cloud.ply") -> list[ReconstructionArtifact]:
    return learned_geometry_expected_outputs(primary_name)


def _list_frame_sidecar_files(root: Path, frame_key: str) -> list[Path]:
    sidecar_dir = _resolve_inside_source(root, frame_key)
    if not sidecar_dir.is_dir():
        return []
    allowed_extensions = SUPPORTED_FRAME_SIDECAR_EXTENSIONS[frame_key]
    files = [path.resolve() for path in sidecar_dir.rglob("*") if path.is_file() and path.suffix.lower() in allowed_extensions]
    for path in files:
        _ensure_inside_source(path, root)
    return sorted(files)


def _read_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise LearnedGeometryImportError(f"Learned geometry completion metadata field {field_name} must be a string list.")
    return sorted(value)


def _read_frame_index_map(value: Any) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, list) or any(not isinstance(item, int) or item < 0 for item in value):
        raise LearnedGeometryImportError("Learned geometry frame_index_map must be a list of non-negative integers.")
    return list(value)


def _require_file(root: Path, relative_path: str, error_message: str) -> Path:
    path = _resolve_inside_source(root, relative_path)
    if not path.is_file():
        raise LearnedGeometryImportError(error_message)
    return path


def _read_json(path: Path, error_message: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LearnedGeometryImportError(error_message) from exc
    if not isinstance(payload, dict):
        raise LearnedGeometryImportError(error_message)
    return payload


def _resolve_inside_source(root: Path, requested_path: str | Path) -> Path:
    candidate = Path(requested_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise LearnedGeometryImportError("Learned geometry source path escaped source_dir.")
    resolved = (root / candidate).resolve()
    _ensure_inside_source(resolved, root)
    return resolved


def _ensure_inside_source(path: Path, root: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise LearnedGeometryImportError("Learned geometry source path escaped source_dir.") from exc
