from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from app.services.project_store import ProjectStore


MAX_DEBUG_FRAME_CLOUD_POINTS = 50_000
OUTPUT_RELATIVE_PATH = Path("reconstruction") / "debug-frame-room.ply"
METADATA_RELATIVE_PATH = Path("metadata") / "debug_frame_cloud.json"
FRAME_METADATA_RELATIVE_PATH = Path("metadata") / "frame_extraction.json"


class DebugFrameCloudService:
    def __init__(self, project_store: ProjectStore) -> None:
        self.project_store = project_store

    def generate(self, project_id: str, max_points: int = MAX_DEBUG_FRAME_CLOUD_POINTS) -> dict[str, Any]:
        if max_points < 1 or max_points > MAX_DEBUG_FRAME_CLOUD_POINTS:
            raise ValueError(f"max_points must be between 1 and {MAX_DEBUG_FRAME_CLOUD_POINTS}.")

        project_dir = self.project_store.get_project_dir(project_id)
        frame_metadata_path = (project_dir / FRAME_METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(frame_metadata_path, project_dir)
        if not frame_metadata_path.is_file():
            raise ValueError("No extracted frames metadata was found. Extract frames before creating a debug 3D preview.")

        frame_metadata = _read_json(frame_metadata_path)
        frames_dir = _resolve_inside_project(project_dir, frame_metadata.get("frames_dir") or "frames")
        if not frames_dir.is_dir():
            raise ValueError("Extracted frames directory was not found. Extract frames before creating a debug 3D preview.")

        frame_paths = sorted(path for path in frames_dir.iterdir() if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"})
        if not frame_paths:
            raise ValueError("No extracted frame images were found. Extract frames before creating a debug 3D preview.")

        points = _sample_frame_points(frame_paths, max_points)
        output_path = (project_dir / OUTPUT_RELATIVE_PATH).resolve()
        metadata_path = (project_dir / METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(output_path, project_dir)
        _ensure_inside_project(metadata_path, project_dir)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        _write_ascii_ply(output_path, points)
        generated_at = datetime.now(UTC).isoformat()
        metadata = {
            "project_id": project_id,
            "artifact_type": "debug_frame_cloud_ply",
            "mode": "debug",
            "not_reconstruction": True,
            "generated_at": generated_at,
            "source_metadata": FRAME_METADATA_RELATIVE_PATH.as_posix(),
            "frames_dir": frames_dir.relative_to(project_dir).as_posix(),
            "frame_count": len(frame_paths),
            "sampled_points": len(points),
            "max_points": max_points,
            "output_path": OUTPUT_RELATIVE_PATH.as_posix(),
            "warning": "Frame Room Cloud is a viewer/debug point cloud sampled from frames. It is not a reconstruction.",
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return metadata


def _sample_frame_points(frame_paths: list[Path], max_points: int) -> list[tuple[float, float, float, int, int, int]]:
    target_per_frame = max(1, max_points // len(frame_paths))
    points: list[tuple[float, float, float, int, int, int]] = []
    arc_radians = math.radians(55)
    radius = 2.2

    for frame_index, frame_path in enumerate(frame_paths):
        with Image.open(frame_path) as image:
            rgb_image = image.convert("RGB")
            width, height = rgb_image.size
            if width < 1 or height < 1:
                continue

            step = max(1, math.ceil(math.sqrt((width * height) / target_per_frame)))
            angle = 0.0 if len(frame_paths) == 1 else -arc_radians / 2 + arc_radians * (frame_index / (len(frame_paths) - 1))
            center_x = math.sin(angle) * radius
            center_z = radius - math.cos(angle) * radius
            right_x = math.cos(angle)
            right_z = math.sin(angle)
            plane_width = 1.35
            plane_height = plane_width * height / width

            for y in range(0, height, step):
                for x in range(0, width, step):
                    if len(points) >= max_points:
                        return points
                    red, green, blue = rgb_image.getpixel((x, y))
                    u = ((x / max(width - 1, 1)) - 0.5) * plane_width
                    v = (0.5 - (y / max(height - 1, 1))) * plane_height
                    point_x = center_x + right_x * u
                    point_y = v
                    point_z = center_z + right_z * u
                    points.append((point_x, point_y, point_z, red, green, blue))

    return points


def _write_ascii_ply(path: Path, points: list[tuple[float, float, float, int, int, int]]) -> None:
    header = [
        "ply",
        "format ascii 1.0",
        "comment RoomSplat debug_frame_cloud_ply; viewer/debug artifact only.",
        "comment Frame Room Cloud is sampled from extracted frames and is not a reconstruction.",
        f"element vertex {len(points)}",
        "property float x",
        "property float y",
        "property float z",
        "property uchar red",
        "property uchar green",
        "property uchar blue",
        "end_header",
    ]
    lines = [*header]
    lines.extend(f"{x:.6f} {y:.6f} {z:.6f} {red} {green} {blue}" for x, y, z, red, green, blue in points)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Frame extraction metadata could not be read.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Frame extraction metadata is invalid.")
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
        raise ValueError("Debug frame cloud path escaped the project directory.") from exc
