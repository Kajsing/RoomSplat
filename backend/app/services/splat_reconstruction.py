from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.services.project_store import ProjectStore
from pipeline.adapters.nerfstudio_splat_runner import (
    NerfstudioSplatPaths,
    NerfstudioSplatRunner,
    NerfstudioSplatRunnerError,
)


FRAME_METADATA_RELATIVE_PATH = Path("metadata") / "frame_extraction.json"
POINT_RECONSTRUCTION_METADATA_RELATIVE_PATH = Path("metadata") / "reconstruction.json"
SPLAT_METADATA_RELATIVE_PATH = Path("metadata") / "splat_reconstruction.json"
SPLAT_OUTPUT_RELATIVE_PATH = Path("reconstruction") / "splat.ply"
NERFSTUDIO_DATASET_RELATIVE_PATH = Path("reconstruction") / "nerfstudio-dataset"
NERFSTUDIO_OUTPUT_ROOT_RELATIVE_PATH = Path("reconstruction") / "nerfstudio-output"
NERFSTUDIO_EXPORT_ROOT_RELATIVE_PATH = Path("reconstruction") / "nerfstudio-export"
SUPPORTED_FRAME_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class SplatReconstructionService:
    def __init__(
        self,
        project_store: ProjectStore,
        *,
        ns_process_data_path: str | None = None,
        ns_train_path: str | None = None,
        ns_export_path: str | None = None,
        nerfstudio_bin_dir: str | None = None,
        nerfstudio_python_path: str | None = None,
        ffmpeg_path: str | None = None,
        colmap_path: str | None = None,
    ) -> None:
        self.project_store = project_store
        self.ns_process_data_path = ns_process_data_path
        self.ns_train_path = ns_train_path
        self.ns_export_path = ns_export_path
        self.nerfstudio_bin_dir = nerfstudio_bin_dir
        self.nerfstudio_python_path = nerfstudio_python_path
        self.ffmpeg_path = ffmpeg_path
        self.colmap_path = colmap_path

    def reconstruct_splat(
        self,
        project_id: str,
        *,
        method: Any = "splatfacto",
        max_iterations: Any = None,
    ) -> dict[str, Any]:
        project_dir = self.project_store.get_project_dir(project_id)
        frame_metadata = self._read_frame_metadata(project_dir)
        frames_dir = _resolve_inside_project(project_dir, frame_metadata.get("frames_dir") or "frames")
        frame_paths = _list_frame_paths(frames_dir)
        if not frame_paths:
            raise ValueError("No extracted frame images were found. Extract frames before running splat reconstruction.")
        if len(frame_paths) < 3:
            raise ValueError("At least 3 extracted frames are required for splat reconstruction.")

        clean_method = _read_method(method)
        clean_max_iterations = _read_optional_positive_int(max_iterations, "max_iterations")
        run_id = uuid4().hex
        paths = NerfstudioSplatPaths(
            frames_dir=frames_dir,
            dataset_dir=(project_dir / NERFSTUDIO_DATASET_RELATIVE_PATH).resolve(),
            output_dir=(project_dir / NERFSTUDIO_OUTPUT_ROOT_RELATIVE_PATH / run_id).resolve(),
            export_dir=(project_dir / NERFSTUDIO_EXPORT_ROOT_RELATIVE_PATH / run_id).resolve(),
            final_splat_ply=(project_dir / SPLAT_OUTPUT_RELATIVE_PATH).resolve(),
        )
        metadata_path = (project_dir / SPLAT_METADATA_RELATIVE_PATH).resolve()
        for path in [paths.dataset_dir, paths.output_dir, paths.export_dir, paths.final_splat_ply, metadata_path]:
            _ensure_inside_project(path, project_dir)

        runner = NerfstudioSplatRunner(
            ns_process_data_path=self.ns_process_data_path,
            ns_train_path=self.ns_train_path,
            ns_export_path=self.ns_export_path,
            nerfstudio_bin_dir=self.nerfstudio_bin_dir,
            nerfstudio_python_path=self.nerfstudio_python_path,
            ffmpeg_path=self.ffmpeg_path,
            colmap_path=self.colmap_path,
        )
        readiness = runner.assess()
        process_command, train_command, export_command = _safe_command_preview(runner, paths, clean_method, clean_max_iterations)
        base_metadata = self._base_metadata(
            project_id=project_id,
            project_dir=project_dir,
            frames_dir=frames_dir,
            frame_paths=frame_paths,
            frame_metadata=frame_metadata,
            method=clean_method,
            max_iterations=clean_max_iterations,
            readiness=readiness,
            process_command=process_command,
            train_command=train_command,
            export_command=export_command,
        )

        if not readiness.is_ready:
            metadata = {
                **base_metadata,
                "status": readiness.status,
                "is_reconstruction": False,
                "not_reconstruction": True,
                "output_path": None,
                "warning": readiness.summary,
            }
            _write_metadata(metadata_path, metadata)
            return metadata

        try:
            run_result = runner.run(paths, method=clean_method, max_iterations=clean_max_iterations)
        except NerfstudioSplatRunnerError as exc:
            metadata = {
                **base_metadata,
                "status": "failed",
                "is_reconstruction": False,
                "not_reconstruction": True,
                "output_path": None,
                "warning": str(exc),
            }
            _write_metadata(metadata_path, metadata)
            raise ValueError(str(exc)) from exc

        metadata = {
            **base_metadata,
            "status": "succeeded",
            "is_reconstruction": True,
            "not_reconstruction": False,
            "output_path": SPLAT_OUTPUT_RELATIVE_PATH.as_posix(),
            "warning": None,
            "nerfstudio": {
                "dataset_dir": run_result.paths.dataset_dir.relative_to(project_dir).as_posix(),
                "output_dir": run_result.paths.output_dir.relative_to(project_dir).as_posix(),
                "export_dir": run_result.paths.export_dir.relative_to(project_dir).as_posix(),
                "config_path": run_result.config_path.relative_to(project_dir).as_posix(),
                "exported_ply": run_result.exported_ply.relative_to(project_dir).as_posix(),
                "command_count": run_result.command_count,
            },
        }
        _write_metadata(metadata_path, metadata)
        return metadata

    def read_metadata(self, project_id: str) -> dict[str, Any]:
        project_dir = self.project_store.get_project_dir(project_id)
        metadata_path = (project_dir / SPLAT_METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(metadata_path, project_dir)
        if not metadata_path.is_file():
            raise ValueError("No splat reconstruction metadata was found.")
        return _read_json(metadata_path, "Splat reconstruction metadata could not be read.")

    def _read_frame_metadata(self, project_dir: Path) -> dict[str, Any]:
        metadata_path = (project_dir / FRAME_METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(metadata_path, project_dir)
        if not metadata_path.is_file():
            raise ValueError("No extracted frames metadata was found. Extract frames before running splat reconstruction.")
        return _read_json(metadata_path, "Frame extraction metadata could not be read.")

    def _base_metadata(
        self,
        *,
        project_id: str,
        project_dir: Path,
        frames_dir: Path,
        frame_paths: list[Path],
        frame_metadata: dict[str, Any],
        method: str,
        max_iterations: int | None,
        readiness: Any,
        process_command: list[str],
        train_command: list[str],
        export_command: list[str],
    ) -> dict[str, Any]:
        source_point_metadata_path = (project_dir / POINT_RECONSTRUCTION_METADATA_RELATIVE_PATH).resolve()
        has_point_metadata = source_point_metadata_path.is_file() and _is_inside_project(source_point_metadata_path, project_dir)
        return {
            "project_id": project_id,
            "artifact_type": "splat_ply",
            "mode": "reconstruction",
            "reconstruction_type": "gaussian_splat",
            "debug": False,
            "placeholder": False,
            "adapter": "nerfstudio-splatfacto",
            "generated_at": datetime.now(UTC).isoformat(),
            "source_metadata": FRAME_METADATA_RELATIVE_PATH.as_posix(),
            "source_point_cloud_metadata": POINT_RECONSTRUCTION_METADATA_RELATIVE_PATH.as_posix() if has_point_metadata else None,
            "frames_dir": frames_dir.relative_to(project_dir).as_posix(),
            "input_frame_count": len(frame_paths),
            "source_frame_count": frame_metadata.get("extracted_frame_count", len(frame_paths)),
            "params": {
                "method": method,
                "max_iterations": max_iterations,
            },
            "readiness": _to_jsonable(readiness),
            "commands": {
                "process_data": process_command,
                "train": train_command,
                "export": export_command,
            },
            "local_only": True,
            "generated_data_rules": "Generated datasets, outputs, checkpoints, and splat exports stay under the ignored project data directory.",
        }


def _safe_command_preview(
    runner: NerfstudioSplatRunner,
    paths: NerfstudioSplatPaths,
    method: str,
    max_iterations: int | None,
) -> tuple[list[str], list[str], list[str]]:
    try:
        return runner.build_commands(paths, method=method, max_iterations=max_iterations)
    except NerfstudioSplatRunnerError:
        return (
            ["ns-process-data", "images", "--data", str(paths.frames_dir), "--output-dir", str(paths.dataset_dir)],
            ["ns-train", method, "--data", str(paths.dataset_dir), "--output-dir", str(paths.output_dir)],
            ["ns-export", "gaussian-splat", "--load-config", "<config.yml>", "--output-dir", str(paths.export_dir)],
        )


def _read_method(value: Any) -> str:
    method = str(value or "splatfacto")
    if method not in {"splatfacto", "splatfacto-big"}:
        raise ValueError("method must be 'splatfacto' or 'splatfacto-big'.")
    return method


def _read_optional_positive_int(value: Any, name: str) -> int | None:
    if value is None or value == "":
        return None
    try:
        clean_value = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive integer.") from exc
    if clean_value < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return clean_value


def _list_frame_paths(frames_dir: Path) -> list[Path]:
    if not frames_dir.is_dir():
        raise ValueError("Extracted frames directory was not found. Extract frames before running splat reconstruction.")
    return sorted(path for path in frames_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_FRAME_EXTENSIONS)


def _read_json(path: Path, error_message: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(error_message) from exc
    if not isinstance(payload, dict):
        raise ValueError(error_message)
    return payload


def _write_metadata(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
        raise ValueError("Splat reconstruction path escaped the project directory.") from exc


def _is_inside_project(path: Path, project_dir: Path) -> bool:
    try:
        path.resolve().relative_to(project_dir.resolve())
        return True
    except ValueError:
        return False


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value
