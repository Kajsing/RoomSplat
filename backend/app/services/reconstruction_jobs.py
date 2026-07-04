from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services.project_store import ProjectStore
from pipeline.adapters.colmap_sparse_runner import ColmapRunnerError, ColmapSparseReconstructionRunner


FRAME_METADATA_RELATIVE_PATH = Path("metadata") / "frame_extraction.json"
RECONSTRUCTION_METADATA_RELATIVE_PATH = Path("metadata") / "reconstruction.json"
OUTPUT_RELATIVE_PATH = Path("reconstruction") / "sparse-point-cloud.ply"
WORKSPACE_ROOT_RELATIVE_PATH = Path("reconstruction") / "colmap-workspace"
SUPPORTED_FRAME_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class ReconstructionService:
    def __init__(self, project_store: ProjectStore, colmap_path: str | None = None) -> None:
        self.project_store = project_store
        self.colmap_path = colmap_path

    def reconstruct_point_cloud(
        self,
        project_id: str,
        *,
        matcher: Any = "exhaustive",
        use_gpu: Any = False,
        preset: Any = "balanced",
    ) -> dict[str, Any]:
        project_dir = self.project_store.get_project_dir(project_id)
        frame_metadata = self._read_frame_metadata(project_dir)
        frames_dir = _resolve_inside_project(project_dir, frame_metadata.get("frames_dir") or "frames")
        frame_paths = _list_frame_paths(frames_dir)
        if not frame_paths:
            raise ValueError("No extracted frame images were found. Extract frames before running point cloud reconstruction.")
        if len(frame_paths) < 3:
            raise ValueError("At least 3 extracted frames are required for COLMAP sparse reconstruction.")

        clean_matcher = _read_matcher(matcher)
        clean_use_gpu = _read_bool(use_gpu)
        clean_preset = _read_preset(preset)
        preset_profile = _preset_profile(clean_preset)
        output_path = (project_dir / OUTPUT_RELATIVE_PATH).resolve()
        metadata_path = (project_dir / RECONSTRUCTION_METADATA_RELATIVE_PATH).resolve()
        workspace_dir = (project_dir / WORKSPACE_ROOT_RELATIVE_PATH / uuid4().hex).resolve()
        _ensure_inside_project(output_path, project_dir)
        _ensure_inside_project(metadata_path, project_dir)
        _ensure_inside_project(workspace_dir, project_dir)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        try:
            run_result = ColmapSparseReconstructionRunner(
                executable=self.colmap_path,
            ).run(
                frames_dir=frames_dir,
                workspace_dir=workspace_dir,
                output_ply=output_path,
                matcher=clean_matcher,
                use_gpu=clean_use_gpu,
            )
        except ColmapRunnerError as exc:
            raise ValueError(str(exc)) from exc

        generated_at = datetime.now(UTC).isoformat()
        quality = _quality_note(run_result.registered_image_count, run_result.ply_point_count)
        metadata = {
            "project_id": project_id,
            "artifact_type": "point_cloud_ply",
            "mode": "reconstruction",
            "reconstruction_type": "sparse_point_cloud",
            "is_reconstruction": True,
            "not_reconstruction": False,
            "debug": False,
            "placeholder": False,
            "adapter": "colmap",
            "generated_at": generated_at,
            "source_metadata": FRAME_METADATA_RELATIVE_PATH.as_posix(),
            "frames_dir": frames_dir.relative_to(project_dir).as_posix(),
            "input_frame_count": len(frame_paths),
            "source_frame_count": frame_metadata.get("extracted_frame_count", len(frame_paths)),
            "registered_frame_count": run_result.registered_image_count,
            "sparse_point_count": run_result.sparse_point_count,
            "ply_point_count": run_result.ply_point_count,
            "cameras": _serialize_cameras(run_result),
            "registered_images": _serialize_registered_images(run_result),
            "camera_path": _serialize_camera_path(run_result),
            "trajectory_bounds": _serialize_trajectory_bounds(run_result),
            "quality": quality,
            "params": {
                "preset": clean_preset,
                "matcher": clean_matcher,
                "use_gpu": clean_use_gpu,
                "recommended_frame_stride": preset_profile["recommended_frame_stride"],
                "recommended_max_frames": preset_profile["recommended_max_frames"],
                "description": preset_profile["description"],
            },
            "colmap": {
                "executable": run_result.executable,
                "command_count": run_result.command_count,
                "workspace": run_result.workspace_dir.relative_to(project_dir).as_posix(),
            },
            "output_path": OUTPUT_RELATIVE_PATH.as_posix(),
            "warning": quality["warning"],
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return metadata

    def read_metadata(self, project_id: str) -> dict[str, Any]:
        project_dir = self.project_store.get_project_dir(project_id)
        metadata_path = (project_dir / RECONSTRUCTION_METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(metadata_path, project_dir)
        if not metadata_path.is_file():
            raise ValueError("No reconstruction metadata was found.")
        return _read_json(metadata_path, "Reconstruction metadata could not be read.")

    def _read_frame_metadata(self, project_dir: Path) -> dict[str, Any]:
        metadata_path = (project_dir / FRAME_METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(metadata_path, project_dir)
        if not metadata_path.is_file():
            raise ValueError("No extracted frames metadata was found. Extract frames before running point cloud reconstruction.")
        return _read_json(metadata_path, "Frame extraction metadata could not be read.")


def _quality_note(registered_frame_count: int, point_count: int) -> dict[str, Any]:
    too_sparse = registered_frame_count < 3 or point_count < 50
    if too_sparse:
        return {
            "status": "too_sparse",
            "warning": "COLMAP produced a sparse result. Try more overlapping frames, slower camera motion, and textured surfaces.",
        }
    return {
        "status": "inspectable",
        "warning": None,
    }


def _read_matcher(value: Any) -> str:
    matcher = str(value or "exhaustive")
    if matcher not in {"exhaustive", "sequential"}:
        raise ValueError("matcher must be 'exhaustive' or 'sequential'.")
    return matcher


def _read_preset(value: Any) -> str:
    preset = str(value or "balanced")
    if preset not in {"quick", "balanced", "detail"}:
        raise ValueError("preset must be 'quick', 'balanced', or 'detail'.")
    return preset


def _preset_profile(preset: str) -> dict[str, Any]:
    profiles = {
        "quick": {
            "recommended_frame_stride": 3,
            "recommended_max_frames": 24,
            "description": "Fast inspection run for checking overlap and artifact flow.",
        },
        "balanced": {
            "recommended_frame_stride": 2,
            "recommended_max_frames": 60,
            "description": "Default local run for comparing camera path and sparse points.",
        },
        "detail": {
            "recommended_frame_stride": 1,
            "recommended_max_frames": 120,
            "description": "Slower run for denser overlap before future splat training.",
        },
    }
    return profiles[preset]


def _read_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        if value.lower() in {"1", "true", "yes", "on"}:
            return True
        if value.lower() in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, int):
        return bool(value)
    raise ValueError("use_gpu must be a boolean.")


def _serialize_cameras(run_result: Any) -> list[dict[str, Any]]:
    metadata = getattr(run_result, "model_metadata", None)
    cameras = getattr(metadata, "cameras", ()) if metadata else ()
    return [
        {
            "camera_id": camera.camera_id,
            "model": camera.model,
            "width": camera.width,
            "height": camera.height,
            "params": list(camera.params),
        }
        for camera in cameras
    ]


def _serialize_registered_images(run_result: Any) -> list[dict[str, Any]]:
    metadata = getattr(run_result, "model_metadata", None)
    registered_images = getattr(metadata, "registered_images", ()) if metadata else ()
    return [
        {
            "image_id": image.image_id,
            "camera_id": image.camera_id,
            "name": image.name,
            "qvec": list(image.qvec),
            "tvec": list(image.tvec),
            "center": {"x": image.center[0], "y": image.center[1], "z": image.center[2]},
        }
        for image in registered_images
    ]


def _serialize_camera_path(run_result: Any) -> list[dict[str, Any]]:
    metadata = getattr(run_result, "model_metadata", None)
    registered_images = getattr(metadata, "registered_images", ()) if metadata else ()
    return [
        {
            "image_id": image.image_id,
            "name": image.name,
            "position": {"x": image.center[0], "y": image.center[1], "z": image.center[2]},
        }
        for image in registered_images
    ]


def _serialize_trajectory_bounds(run_result: Any) -> dict[str, dict[str, float]] | None:
    metadata = getattr(run_result, "model_metadata", None)
    bounds = getattr(metadata, "trajectory_bounds", None) if metadata else None
    if bounds is None:
        return None
    return {
        "min": {"x": bounds.min[0], "y": bounds.min[1], "z": bounds.min[2]},
        "max": {"x": bounds.max[0], "y": bounds.max[1], "z": bounds.max[2]},
    }


def _list_frame_paths(frames_dir: Path) -> list[Path]:
    if not frames_dir.is_dir():
        raise ValueError("Extracted frames directory was not found. Extract frames before running point cloud reconstruction.")
    return sorted(path for path in frames_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_FRAME_EXTENSIONS)


def _read_json(path: Path, error_message: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(error_message) from exc
    if not isinstance(payload, dict):
        raise ValueError(error_message)
    return payload


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
        raise ValueError("Reconstruction path escaped the project directory.") from exc
