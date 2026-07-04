from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image

from app.services.project_store import ProjectStore


MAX_DEBUG_FRAME_CLOUD_POINTS = 50_000
DEFAULT_FRAME_STEP = 1
DEFAULT_ARC_DEGREES = 55.0
DEFAULT_PLANE_WIDTH = 1.35
MAX_ARC_DEGREES = 180.0
MAX_PLANE_WIDTH = 10.0
OUTPUT_RELATIVE_PATH = Path("reconstruction") / "debug-frame-room.ply"
METADATA_RELATIVE_PATH = Path("metadata") / "debug_frame_cloud.json"
FRAME_METADATA_RELATIVE_PATH = Path("metadata") / "frame_extraction.json"


class DebugFrameCloudService:
    def __init__(self, project_store: ProjectStore) -> None:
        self.project_store = project_store

    def generate(
        self,
        project_id: str,
        max_points: Any = MAX_DEBUG_FRAME_CLOUD_POINTS,
        frame_step: Any = DEFAULT_FRAME_STEP,
        arc_degrees: Any = DEFAULT_ARC_DEGREES,
        plane_width: Any = DEFAULT_PLANE_WIDTH,
    ) -> dict[str, Any]:
        options = _validate_options(max_points, frame_step, arc_degrees, plane_width)
        project_dir = self.project_store.get_project_dir(project_id)
        frame_metadata_path = (project_dir / FRAME_METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(frame_metadata_path, project_dir)
        if not frame_metadata_path.is_file():
            raise ValueError("No extracted frames metadata was found. Extract frames before creating debug frame planes.")

        frame_metadata = _read_json(frame_metadata_path)
        frames_dir = _resolve_inside_project(project_dir, frame_metadata.get("frames_dir") or "frames")
        if not frames_dir.is_dir():
            raise ValueError("Extracted frames directory was not found. Extract frames before creating debug frame planes.")

        frame_paths = sorted(path for path in frames_dir.iterdir() if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"})
        if not frame_paths:
            raise ValueError("No extracted frame images were found. Extract frames before creating debug frame planes.")

        selected_frame_paths = frame_paths[:: options["frame_step"]]
        if not selected_frame_paths:
            raise ValueError("No frames were selected for debug frame planes.")
        if len(selected_frame_paths) > options["max_points"]:
            selected_frame_paths = selected_frame_paths[: options["max_points"]]

        points, frame_planes = _sample_frame_points(selected_frame_paths, project_dir, options)
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
            "source_frame_count": len(frame_paths),
            "frame_count": len(selected_frame_paths),
            "sampled_points": len(points),
            "max_points": options["max_points"],
            "params": options,
            "frame_planes": frame_planes,
            "output_path": OUTPUT_RELATIVE_PATH.as_posix(),
            "warning": "Debug frame planes are viewer/debug points sampled from flat frames and placed in 3D. This is not a reconstruction.",
        }
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        return metadata

    def read_metadata(self, project_id: str) -> dict[str, Any]:
        project_dir = self.project_store.get_project_dir(project_id)
        metadata_path = (project_dir / METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(metadata_path, project_dir)
        if not metadata_path.is_file():
            raise ValueError("No debug frame cloud metadata was found.")
        return _read_json(metadata_path)


def _validate_options(max_points: Any, frame_step: Any, arc_degrees: Any, plane_width: Any) -> dict[str, Any]:
    clean_max_points = _read_int(max_points, "max_points")
    clean_frame_step = _read_int(frame_step, "frame_step")
    clean_arc_degrees = _read_float(arc_degrees, "arc_degrees")
    clean_plane_width = _read_float(plane_width, "plane_width")

    if clean_max_points < 1 or clean_max_points > MAX_DEBUG_FRAME_CLOUD_POINTS:
        raise ValueError(f"max_points must be between 1 and {MAX_DEBUG_FRAME_CLOUD_POINTS}.")
    if clean_frame_step < 1:
        raise ValueError("frame_step must be at least 1.")
    if clean_arc_degrees <= 0 or clean_arc_degrees > MAX_ARC_DEGREES:
        raise ValueError(f"arc_degrees must be greater than 0 and at most {MAX_ARC_DEGREES:.0f}.")
    if clean_plane_width <= 0 or clean_plane_width > MAX_PLANE_WIDTH:
        raise ValueError(f"plane_width must be greater than 0 and at most {MAX_PLANE_WIDTH:.0f}.")

    return {
        "max_points": clean_max_points,
        "frame_step": clean_frame_step,
        "arc_degrees": clean_arc_degrees,
        "plane_width": clean_plane_width,
    }


def _sample_frame_points(
    frame_paths: list[Path],
    project_dir: Path,
    options: dict[str, Any],
) -> tuple[list[tuple[float, float, float, int, int, int]], list[dict[str, Any]]]:
    max_points = int(options["max_points"])
    base_target = max_points // len(frame_paths)
    remainder = max_points % len(frame_paths)
    points: list[tuple[float, float, float, int, int, int]] = []
    frame_planes: list[dict[str, Any]] = []
    arc_radians = math.radians(float(options["arc_degrees"]))
    plane_width = float(options["plane_width"])
    radius = max(2.2, (len(frame_paths) - 1) * plane_width * 0.3)

    for frame_index, frame_path in enumerate(frame_paths):
        with Image.open(frame_path) as image:
            rgb_image = image.convert("RGB")
            width, height = rgb_image.size
            if width < 1 or height < 1:
                continue

            point_budget = base_target + (1 if frame_index < remainder else 0)
            step = max(1, math.ceil(math.sqrt((width * height) / point_budget)))
            angle = 0.0 if len(frame_paths) == 1 else -arc_radians / 2 + arc_radians * (frame_index / (len(frame_paths) - 1))
            center_x = math.sin(angle) * radius
            center_z = radius - math.cos(angle) * radius
            right_x = math.cos(angle)
            right_z = math.sin(angle)
            plane_height = plane_width * height / width
            plane_point_count = 0

            for y in range(0, height, step):
                for x in range(0, width, step):
                    if plane_point_count >= point_budget:
                        break
                    red, green, blue = rgb_image.getpixel((x, y))
                    u = ((x / max(width - 1, 1)) - 0.5) * plane_width
                    v = (0.5 - (y / max(height - 1, 1))) * plane_height
                    point_x = center_x + right_x * u
                    point_y = v
                    point_z = center_z + right_z * u
                    points.append((point_x, point_y, point_z, red, green, blue))
                    plane_point_count += 1
                if plane_point_count >= point_budget:
                    break

            frame_planes.append(
                {
                    "frame_index": frame_index,
                    "source_frame": frame_path.relative_to(project_dir).as_posix(),
                    "position": {
                        "x": round(center_x, 6),
                        "y": 0.0,
                        "z": round(center_z, 6),
                    },
                    "angle_degrees": round(math.degrees(angle), 6),
                    "point_count": plane_point_count,
                    "image_width": width,
                    "image_height": height,
                    "plane_width": round(plane_width, 6),
                    "plane_height": round(plane_height, 6),
                }
            )

    return points, frame_planes


def _write_ascii_ply(path: Path, points: list[tuple[float, float, float, int, int, int]]) -> None:
    header = [
        "ply",
        "format ascii 1.0",
        "comment RoomSplat debug_frame_cloud_ply; viewer/debug artifact only.",
        "comment Debug frame planes are sampled from extracted frames and are not a reconstruction.",
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


def _read_int(value: Any, field_name: str) -> int:
    try:
        clean_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be an integer.") from exc
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(f"{field_name} must be an integer.")
    return clean_value


def _read_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number.") from exc


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
