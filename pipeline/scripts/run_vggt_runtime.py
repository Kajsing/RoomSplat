from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
DEFAULT_VGGT_RESOLUTION = 518


class VggtRuntimeError(RuntimeError):
    pass


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a local VGGT smoke inference for RoomSplat.")
    parser.add_argument("--frames-dir", required=True, help="Directory containing selected frames from RoomSplat.")
    parser.add_argument("--output-dir", required=True, help="Directory where the completed learned output folder is written.")
    parser.add_argument("--checkpoint", required=True, help="Local VGGT checkpoint path. No downloads are performed.")
    parser.add_argument("--max-frames", type=int, required=True, help="Maximum selected frames supplied by RoomSplat.")
    parser.add_argument("--image-max-size", type=int, required=True, help="Requested image size cap from RoomSplat.")
    parser.add_argument("--precision", choices=["fp32", "fp16", "bfloat16"], required=True, help="Inference precision.")
    parser.add_argument("--frame-index-map", required=True, help="Comma-separated original frame indices for selected frames.")
    parser.add_argument("--allow-cpu-offload", action="store_true", help="Accepted for contract compatibility; VGGT wrapper does not offload yet.")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto", help="Inference device.")
    parser.add_argument("--max-points", type=int, default=100_000, help="Maximum points written to points.ply.")
    parser.add_argument("--confidence-threshold", type=float, default=0.0, help="Minimum world point confidence for exported points.")
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs and write blocked diagnostics without importing VGGT.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run(args)
        return 0
    except VggtRuntimeError as exc:
        print(f"ROOMSPLAT_VGGT_BLOCKED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ROOMSPLAT_VGGT_FAILED: {exc}", file=sys.stderr)
        return 1


def run(args: argparse.Namespace) -> None:
    frames_dir = Path(args.frames_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    checkpoint = Path(args.checkpoint).resolve()
    if not frames_dir.is_dir():
        raise VggtRuntimeError(f"frames-dir was not found: {frames_dir}")
    if not checkpoint.is_file():
        raise VggtRuntimeError(f"checkpoint was not found: {checkpoint}")
    if args.max_frames < 1:
        raise VggtRuntimeError("max-frames must be at least 1.")
    if args.max_points < 1:
        raise VggtRuntimeError("max-points must be at least 1.")
    frame_paths = list_image_paths(frames_dir)[: args.max_frames]
    if not frame_paths:
        raise VggtRuntimeError("No selected frames were found.")
    frame_index_map = parse_frame_index_map(args.frame_index_map, len(frame_paths))
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        write_blocked_diagnostics(output_dir, frame_paths, frame_index_map, args, "dry_run_requested")
        raise VggtRuntimeError("dry-run completed without running VGGT.")

    predictions = run_vggt_inference(frame_paths, checkpoint, args)
    write_roomsplat_output(output_dir, frame_paths, frame_index_map, predictions, args)


def run_vggt_inference(frame_paths: list[Path], checkpoint: Path, args: argparse.Namespace) -> dict[str, Any]:
    try:
        import numpy as np
        import torch
        import torch.nn.functional as torch_functional
        from safetensors.torch import load_file as load_safetensors
        from vggt.models.vggt import VGGT
        from vggt.utils.load_fn import load_and_preprocess_images_square
        from vggt.utils.pose_enc import pose_encoding_to_extri_intri
    except Exception as exc:
        raise VggtRuntimeError(
            "VGGT runtime dependencies are missing. Install VGGT, torch, torchvision, numpy, Pillow, safetensors, and huggingface_hub in the selected local runtime environment."
        ) from exc

    device = choose_device(torch, args.device)
    dtype = choose_dtype(torch, args.precision, device)
    resolution = choose_vggt_resolution(args.image_max_size)
    images, _original_coords = load_and_preprocess_images_square([str(path) for path in frame_paths], target_size=resolution)
    images = images.to(device)
    model = VGGT(img_size=resolution)
    state_dict = load_checkpoint_state_dict(torch, load_safetensors, checkpoint)
    model.load_state_dict(state_dict)
    model.eval()
    model.to(device)

    with torch.no_grad():
        autocast_enabled = device == "cuda" and dtype is not torch.float32
        with torch.cuda.amp.autocast(enabled=autocast_enabled, dtype=dtype):
            output = model(images)

    pose_enc = output.get("pose_enc")
    extrinsic = intrinsic = None
    if pose_enc is not None:
        with torch.cuda.amp.autocast(enabled=False):
            extrinsic, intrinsic = pose_encoding_to_extri_intri(pose_enc, images.shape[-2:])

    world_points = output.get("world_points")
    world_conf = output.get("world_points_conf")
    if world_points is None:
        raise VggtRuntimeError("VGGT did not return world_points; this wrapper needs the point head enabled.")
    if world_points.ndim == 5:
        world_points = world_points.squeeze(0)
    if world_conf is not None and world_conf.ndim == 4:
        world_conf = world_conf.squeeze(0)

    rgb_images = torch_functional.interpolate(images, size=world_points.shape[1:3], mode="bilinear", align_corners=False)
    rgb_images = rgb_images.detach().cpu().numpy().transpose(0, 2, 3, 1)

    return {
        "points": world_points.detach().cpu().numpy(),
        "confidence": None if world_conf is None else world_conf.detach().cpu().numpy(),
        "colors": np.clip(rgb_images * 255, 0, 255).astype(np.uint8),
        "extrinsic": None if extrinsic is None else extrinsic.squeeze(0).detach().cpu().numpy(),
        "intrinsic": None if intrinsic is None else intrinsic.squeeze(0).detach().cpu().numpy(),
        "resolution": resolution,
        "device": device,
        "precision": args.precision,
    }


def write_roomsplat_output(
    output_dir: Path,
    frame_paths: list[Path],
    frame_index_map: list[int],
    predictions: dict[str, Any],
    args: argparse.Namespace,
) -> None:
    points, colors = flatten_points_for_ply(
        predictions["points"],
        predictions["colors"],
        predictions.get("confidence"),
        confidence_threshold=args.confidence_threshold,
        max_points=args.max_points,
    )
    write_ascii_ply(output_dir / "points.ply", points, colors)
    sidecars = ["points"]
    if predictions.get("extrinsic") is not None:
        write_traj_txt(output_dir / "traj.txt", predictions["extrinsic"])
        sidecars.append("pose")
    if predictions.get("intrinsic") is not None:
        write_intrinsics_txt(output_dir / "intrinsics.txt", predictions["intrinsic"], predictions["resolution"])
        sidecars.append("intrinsics")
    write_sampling_json(
        output_dir / "sampling.json",
        frame_paths,
        frame_index_map,
        {
            "adapter": "vggt",
            "resolution": predictions["resolution"],
            "device": predictions["device"],
            "precision": predictions["precision"],
            "max_points": args.max_points,
            "confidence_threshold": args.confidence_threshold,
            "point_count": len(points),
        },
    )
    write_completion_json(output_dir / ".complete.json", frame_index_map, frame_keys=[key for key in sidecars if key != "points"])


def flatten_points_for_ply(
    points: Any,
    colors: Any,
    confidence: Any | None,
    *,
    confidence_threshold: float,
    max_points: int,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    flat_points = _flatten_vectors(points)
    flat_colors = _flatten_vectors(colors)
    flat_conf = _flatten_scalars(confidence) if confidence is not None else [None] * len(flat_points)
    if len(flat_points) != len(flat_colors) or len(flat_points) != len(flat_conf):
        raise VggtRuntimeError("VGGT points, colors, and confidence arrays must align.")

    filtered_points: list[tuple[float, float, float]] = []
    filtered_colors: list[tuple[int, int, int]] = []
    for point, color, conf in zip(flat_points, flat_colors, flat_conf, strict=True):
        parsed_point = tuple(float(value) for value in point)
        if len(parsed_point) != 3 or not all(math.isfinite(value) for value in parsed_point):
            continue
        if conf is not None and (not math.isfinite(float(conf)) or float(conf) < confidence_threshold):
            continue
        filtered_points.append(parsed_point)
        filtered_colors.append(tuple(_clamp_color(int(value)) for value in color))

    if len(filtered_points) > max_points:
        selected = _linspace_indices(len(filtered_points), max_points)
        filtered_points = [filtered_points[index] for index in selected]
        filtered_colors = [filtered_colors[index] for index in selected]
    return filtered_points, filtered_colors


def write_ascii_ply(path: Path, points: list[tuple[float, float, float]], colors: list[tuple[int, int, int]]) -> None:
    if len(points) != len(colors):
        raise VggtRuntimeError("PLY points and colors must have the same length.")
    lines = [
        "ply",
        "format ascii 1.0",
        f"element vertex {len(points)}",
        "property float x",
        "property float y",
        "property float z",
        "property uchar red",
        "property uchar green",
        "property uchar blue",
        "end_header",
    ]
    for point, color in zip(points, colors, strict=True):
        lines.append(
            f"{_format_float(point[0])} {_format_float(point[1])} {_format_float(point[2])} "
            f"{_clamp_color(color[0])} {_clamp_color(color[1])} {_clamp_color(color[2])}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_traj_txt(path: Path, extrinsic: Any) -> None:
    lines = ["# frame_idx r00 r01 r02 tx r10 r11 r12 ty r20 r21 r22 tz"]
    for frame_index, world_to_camera in enumerate(extrinsic):
        camera_to_world = _invert_world_to_camera(world_to_camera)
        values = " ".join(_format_float(float(value)) for row in camera_to_world[:3] for value in row)
        lines.append(f"{frame_index} {values}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_intrinsics_txt(path: Path, intrinsic: Any, resolution: int) -> None:
    lines = ["# frame_idx fx fy cx cy width height"]
    for frame_index, matrix in enumerate(intrinsic):
        lines.append(
            f"{frame_index} {_format_float(_matrix_value(matrix, 0, 0))} {_format_float(_matrix_value(matrix, 1, 1))} "
            f"{_format_float(_matrix_value(matrix, 0, 2))} {_format_float(_matrix_value(matrix, 1, 2))} {resolution} {resolution}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_sampling_json(path: Path, frame_paths: list[Path], frame_index_map: list[int], runtime: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(
            {
                "adapter": "vggt",
                "generated_at": datetime.now(UTC).isoformat(),
                "frame_index_map": frame_index_map,
                "runtime": runtime,
                "selected_frames": [
                    {"bundle_frame_index": index, "source_frame_index": frame_index_map[index], "name": frame.name}
                    for index, frame in enumerate(frame_paths)
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_completion_json(path: Path, frame_index_map: list[int], *, frame_keys: list[str]) -> None:
    path.write_text(
        json.dumps(
            {
                "completed_at": datetime.now(UTC).isoformat(),
                "metadata": {
                    "adapter": "vggt",
                    "schema_version": "roomsplat.vggt_output.v1",
                    "frame_keys": sorted(frame_keys),
                    "global_keys": ["points"],
                    "frame_index_map": frame_index_map,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_blocked_diagnostics(
    output_dir: Path,
    frame_paths: list[Path],
    frame_index_map: list[int],
    args: argparse.Namespace,
    reason: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "blocked_vggt_runtime.json").write_text(
        json.dumps(
            {
                "status": "blocked",
                "reason": reason,
                "generated_at": datetime.now(UTC).isoformat(),
                "frame_count": len(frame_paths),
                "frame_index_map": frame_index_map,
                "image_max_size": args.image_max_size,
                "precision": args.precision,
                "no_auto_downloads": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def list_image_paths(frames_dir: Path) -> list[Path]:
    return sorted(path for path in frames_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS)


def parse_frame_index_map(value: str, expected_count: int) -> list[int]:
    try:
        parsed = [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as exc:
        raise VggtRuntimeError("frame-index-map must contain comma-separated integers.") from exc
    if len(parsed) != expected_count:
        raise VggtRuntimeError(f"frame-index-map contains {len(parsed)} entries, but {expected_count} frames were selected.")
    if any(index < 0 for index in parsed):
        raise VggtRuntimeError("frame-index-map cannot contain negative values.")
    return parsed


def choose_device(torch: Any, requested: str) -> str:
    if requested == "cpu":
        return "cpu"
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise VggtRuntimeError("CUDA was requested, but torch.cuda.is_available() is false.")
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"


def choose_dtype(torch: Any, precision: str, device: str) -> Any:
    if precision == "fp32" or device == "cpu":
        return torch.float32
    if precision == "bfloat16":
        return torch.bfloat16
    return torch.float16


def choose_vggt_resolution(image_max_size: int) -> int:
    if image_max_size < 224:
        raise VggtRuntimeError("image-max-size must be at least 224 for VGGT.")
    if image_max_size >= DEFAULT_VGGT_RESOLUTION:
        return DEFAULT_VGGT_RESOLUTION
    return max(224, int(math.floor(image_max_size / 14) * 14))


def load_checkpoint_state_dict(torch: Any, load_safetensors: Any, checkpoint: Path) -> dict[str, Any]:
    if checkpoint.suffix.lower() == ".safetensors":
        payload = load_safetensors(str(checkpoint), device="cpu")
    else:
        payload = torch.load(str(checkpoint), map_location="cpu")
    if isinstance(payload, dict):
        for key in ("model", "state_dict", "model_state_dict"):
            nested = payload.get(key)
            if isinstance(nested, dict):
                return _strip_module_prefix(nested)
        return _strip_module_prefix(payload)
    raise VggtRuntimeError("Checkpoint did not contain a PyTorch state dict.")


def _strip_module_prefix(state_dict: dict[str, Any]) -> dict[str, Any]:
    return {key.removeprefix("module."): value for key, value in state_dict.items()}


def _invert_world_to_camera(matrix: Any) -> list[list[float]]:
    rows = [[float(value) for value in row] for row in matrix]
    if len(rows) == 4 and all(len(row) == 4 for row in rows):
        rows = rows[:3]
    if len(rows) != 3 or any(len(row) != 4 for row in rows):
        raise VggtRuntimeError("Extrinsic camera matrix must have shape 3x4 or 4x4.")
    rotation = [row[:3] for row in rows]
    translation = [row[3] for row in rows]
    rotation_t = [[rotation[row][column] for row in range(3)] for column in range(3)]
    inverted_translation = [-sum(rotation_t[row][column] * translation[column] for column in range(3)) for row in range(3)]
    return [rotation_t[row] + [inverted_translation[row]] for row in range(3)] + [[0.0, 0.0, 0.0, 1.0]]


def _flatten_vectors(value: Any) -> list[tuple[Any, ...]]:
    if hasattr(value, "reshape"):
        return [tuple(row) for row in value.reshape(-1, value.shape[-1]).tolist()]
    flattened: list[tuple[Any, ...]] = []

    def visit(node: Any) -> None:
        if isinstance(node, (list, tuple)) and node and all(not isinstance(item, (list, tuple)) for item in node):
            flattened.append(tuple(node))
            return
        for item in node:
            visit(item)

    visit(value)
    return flattened


def _flatten_scalars(value: Any) -> list[Any]:
    if hasattr(value, "reshape"):
        return value.reshape(-1).tolist()
    flattened: list[Any] = []

    def visit(node: Any) -> None:
        if isinstance(node, (list, tuple)):
            for item in node:
                visit(item)
        else:
            flattened.append(node)

    visit(value)
    return flattened


def _linspace_indices(length: int, count: int) -> list[int]:
    if count == 1:
        return [0]
    return [round(index * (length - 1) / (count - 1)) for index in range(count)]


def _matrix_value(matrix: Any, row: int, column: int) -> float:
    try:
        return float(matrix[row, column])
    except (TypeError, IndexError):
        return float(matrix[row][column])


def _format_float(value: float) -> str:
    if abs(value) < 1e-10:
        value = 0.0
    return f"{value:.8g}"


def _clamp_color(value: int) -> int:
    return max(0, min(255, int(value)))


if __name__ == "__main__":
    raise SystemExit(main())
