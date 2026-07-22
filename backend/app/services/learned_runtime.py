from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.services.geometry_bundle import GEOMETRY_BUNDLE_RELATIVE_PATH, read_validated_geometry_bundle
from app.services.learned_geometry_import import LearnedGeometryImportService
from app.services.project_store import ProjectStore
from pipeline.adapters.learned_runtime import (
    LearnedRuntimeConfig,
    build_learned_runtime_params,
    materialize_selected_frames,
    preflight_learned_runtime,
    run_learned_runtime_command,
    select_keyframes,
)


FRAME_METADATA_RELATIVE_PATH = Path("metadata") / "frame_extraction.json"
SUPPORTED_FRAME_EXTENSIONS = {".png", ".jpg", ".jpeg"}


class LearnedRuntimeService:
    def __init__(self, project_store: ProjectStore, config: AppConfig) -> None:
        self.project_store = project_store
        self.config = config

    def preflight(self, project_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        runtime_params = build_learned_runtime_params(params)
        project_dir, frame_paths = self._project_frames(project_id)
        runtime_config = self._runtime_config()
        preflight = preflight_learned_runtime(config=runtime_config, params=runtime_params, frame_paths=frame_paths).to_dict()
        result = {
            "project_id": project_id,
            "job_type": "learned_runtime_preflight",
            **preflight,
        }
        metadata_path = (project_dir / "metadata" / "learned_runtime_preflight.json").resolve()
        _ensure_inside_project(metadata_path, project_dir)
        metadata_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result

    def run_smoke(self, project_id: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        runtime_params = build_learned_runtime_params(params)
        project_dir, frame_paths = self._project_frames(project_id)
        runtime_config = self._runtime_config()
        preflight = preflight_learned_runtime(config=runtime_config, params=runtime_params, frame_paths=frame_paths)
        if not preflight.is_ready:
            result = {
                "project_id": project_id,
                "job_type": "learned_runtime_smoke",
                **preflight.to_dict(),
                "output_path": None,
                "imported": False,
            }
            self._write_smoke_metadata(project_dir, result)
            return result

        selected = select_keyframes(frame_paths, runtime_params)
        source_indices = [frame.source_index for frame in selected]
        run_root = _runtime_output_root(project_dir, runtime_params.adapter)
        selected_frames_dir = (run_root / "selected-frames").resolve()
        output_dir = (run_root / "output").resolve()
        _ensure_inside_project(selected_frames_dir, project_dir)
        _ensure_inside_project(output_dir, project_dir)
        materialized_frames = materialize_selected_frames(selected, selected_frames_dir)
        command_result = run_learned_runtime_command(
            config=runtime_config,
            params=runtime_params,
            selected_frames_dir=selected_frames_dir,
            output_dir=output_dir,
            source_indices=source_indices,
        )
        if command_result["returncode"] != 0:
            result = {
                "project_id": project_id,
                "job_type": "learned_runtime_smoke",
                **preflight.to_dict(),
                "status": "failed",
                "summary": "Learned runtime command failed; no geometry was imported.",
                "output_path": None,
                "imported": False,
                "materialized_frames": materialized_frames,
                "runtime_command": command_result,
            }
            self._write_smoke_metadata(project_dir, result)
            return result

        imported = LearnedGeometryImportService(self.project_store).import_output(
            project_id,
            source_dir=output_dir,
            source_adapter=runtime_params.adapter,
            primary_ply="points.ply",
        )
        imported = _annotate_runtime_geometry_bundle(project_dir, runtime_params.adapter, preflight.to_dict())
        result = {
            **imported,
            "job_type": "learned_runtime_smoke",
            "runtime_status": "succeeded",
            "runtime_preflight": preflight.to_dict(),
            "runtime_output_dir": output_dir.relative_to(project_dir).as_posix(),
            "materialized_frames": materialized_frames,
            "runtime_command": command_result,
        }
        self._write_smoke_metadata(project_dir, result)
        return result

    def _runtime_config(self) -> LearnedRuntimeConfig:
        return LearnedRuntimeConfig(
            command=self.config.learned_runtime_command,
            args=self.config.learned_runtime_args,
            python_path=self.config.learned_runtime_python_path,
            checkpoint_path=self.config.learned_checkpoint_path,
            checkpoint_sha256=self.config.learned_checkpoint_sha256,
            model_root=self.config.learned_model_root,
            cache_dir=self.config.learned_cache_dir,
            min_free_vram_mb=self.config.learned_min_free_vram_mb,
            timeout_seconds=self.config.learned_runtime_timeout_seconds,
        )

    def _project_frames(self, project_id: str) -> tuple[Path, list[Path]]:
        project_dir = self.project_store.get_project_dir(project_id)
        metadata_path = (project_dir / FRAME_METADATA_RELATIVE_PATH).resolve()
        _ensure_inside_project(metadata_path, project_dir)
        if not metadata_path.is_file():
            raise ValueError("No extracted frames metadata was found. Extract frames before running learned runtime.")
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Frame extraction metadata is invalid.")
        frames_dir = _resolve_inside_project(project_dir, payload.get("frames_dir") or "frames")
        if not frames_dir.is_dir():
            raise ValueError("Extracted frames directory was not found. Extract frames before running learned runtime.")
        frame_paths = sorted(path for path in frames_dir.iterdir() if path.is_file() and path.suffix.lower() in SUPPORTED_FRAME_EXTENSIONS)
        if not frame_paths:
            raise ValueError("No extracted frame images were found. Extract frames before running learned runtime.")
        return project_dir, frame_paths

    def _write_smoke_metadata(self, project_dir: Path, result: dict[str, Any]) -> None:
        metadata_path = (project_dir / "metadata" / "learned_runtime_smoke.json").resolve()
        _ensure_inside_project(metadata_path, project_dir)
        payload = {**result, "recorded_at": datetime.now(UTC).isoformat()}
        metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _runtime_output_root(project_dir: Path, adapter: str) -> Path:
    slug = "".join(character.lower() if character.isalnum() else "-" for character in adapter).strip("-") or "local-learned-runtime"
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    root = (project_dir / "metadata" / "learned-runtime" / f"{slug}-{timestamp}").resolve()
    _ensure_inside_project(root, project_dir)
    return root


def _annotate_runtime_geometry_bundle(project_dir: Path, adapter: str, preflight: dict[str, Any]) -> dict[str, Any]:
    metadata_path = (project_dir / GEOMETRY_BUNDLE_RELATIVE_PATH).resolve()
    _ensure_inside_project(metadata_path, project_dir)
    payload = json.loads(metadata_path.read_text(encoding="utf-8"))
    existing_warnings = [
        warning
        for warning in payload.get("warnings", [])
        if "No model checkpoint was loaded by RoomSplat" not in str(warning)
    ]
    checkpoint = preflight.get("checkpoint") if isinstance(preflight.get("checkpoint"), dict) else {}
    digest = str(checkpoint.get("sha256") or "")
    digest_note = f" SHA-256: {digest[:12]}..." if digest else ""
    payload["warnings"] = [
        *existing_warnings,
        f"{adapter} learned runtime loaded a local, SHA-256 allowlisted checkpoint through RoomSplat preflight.{digest_note}",
        "This is learned/predicted geometry from a model runtime, not a verified metric reconstruction.",
    ]
    quality = payload.get("quality") if isinstance(payload.get("quality"), dict) else {}
    quality["status"] = "needs_review"
    quality["notes"] = f"Predicted geometry generated by the local {adapter} runtime smoke path. Inspect visually before use."
    payload["quality"] = quality
    rules = payload.get("generated_data_rules") if isinstance(payload.get("generated_data_rules"), dict) else {}
    rules["notes"] = "Learned runtime output was generated locally from selected project frames and imported into the project data folder."
    payload["generated_data_rules"] = rules
    metadata_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return read_validated_geometry_bundle(project_dir).model_dump()


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
        raise ValueError("Learned runtime path escaped the project directory.") from exc
