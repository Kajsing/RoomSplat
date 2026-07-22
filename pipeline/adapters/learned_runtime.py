from __future__ import annotations

import hashlib
import json
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pipeline.adapters.base import DependencyCheck, learned_geometry_expected_outputs


LearnedRuntimeStatus = Literal[
    "ready",
    "blocked_missing_dependencies",
    "blocked_missing_checkpoint",
    "blocked_untrusted_checkpoint",
    "blocked_insufficient_vram",
]
PrecisionMode = Literal["fp32", "fp16", "bfloat16"]


@dataclass(frozen=True)
class LearnedRuntimeConfig:
    command: str | None = None
    args: str | None = None
    python_path: str | None = None
    checkpoint_path: str | None = None
    checkpoint_sha256: str | None = None
    model_root: Path = Path("data") / "models"
    cache_dir: Path = Path("data") / "cache" / "learned-runtime"
    min_free_vram_mb: int = 10_000
    timeout_seconds: int = 30 * 60


@dataclass(frozen=True)
class LearnedRuntimeParams:
    max_frames: int = 12
    frame_step: int = 1
    image_max_size: int = 768
    precision: PrecisionMode = "fp16"
    allow_cpu_offload: bool = False
    adapter: str = "local-learned-runtime"


@dataclass(frozen=True)
class SelectedFrame:
    source_index: int
    source_path: Path


@dataclass(frozen=True)
class LearnedRuntimePreflight:
    adapter: str
    status: LearnedRuntimeStatus
    summary: str
    dependencies: list[DependencyCheck]
    blockers: list[str]
    warnings: list[str]
    next_steps: list[str]
    gpu: dict[str, Any]
    torch: dict[str, Any]
    checkpoint: dict[str, Any]
    runtime_budget: dict[str, Any]
    selected_frame_indices: list[int]
    expected_outputs: list[dict[str, str]]
    generated_data_rules: dict[str, Any]

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"

    def to_dict(self) -> dict[str, Any]:
        return {
            "adapter": self.adapter,
            "status": self.status,
            "summary": self.summary,
            "dependencies": [dependency.__dict__ for dependency in self.dependencies],
            "blockers": self.blockers,
            "warnings": self.warnings,
            "next_steps": self.next_steps,
            "gpu": self.gpu,
            "torch": self.torch,
            "checkpoint": self.checkpoint,
            "runtime_budget": self.runtime_budget,
            "selected_frame_indices": self.selected_frame_indices,
            "expected_outputs": self.expected_outputs,
            "generated_data_rules": self.generated_data_rules,
        }


class LearnedRuntimeError(ValueError):
    pass


def build_learned_runtime_params(params: dict[str, Any] | None = None) -> LearnedRuntimeParams:
    payload = params or {}
    max_frames = _read_int(payload.get("max_frames", 12), "max_frames", minimum=1, maximum=240)
    frame_step = _read_int(payload.get("frame_step", 1), "frame_step", minimum=1, maximum=240)
    image_max_size = _read_int(payload.get("image_max_size", 768), "image_max_size", minimum=128, maximum=4096)
    precision = str(payload.get("precision", "fp16")).strip().lower()
    if precision not in {"fp32", "fp16", "bfloat16"}:
        raise LearnedRuntimeError("precision must be one of fp32, fp16, or bfloat16.")
    adapter = " ".join(str(payload.get("adapter", "local-learned-runtime")).strip().split())
    if not adapter:
        raise LearnedRuntimeError("adapter is required for learned runtime jobs.")
    if len(adapter) > 80:
        raise LearnedRuntimeError("adapter must be 80 characters or fewer.")
    return LearnedRuntimeParams(
        max_frames=max_frames,
        frame_step=frame_step,
        image_max_size=image_max_size,
        precision=precision,  # type: ignore[arg-type]
        allow_cpu_offload=bool(payload.get("allow_cpu_offload", False)),
        adapter=adapter,
    )


def select_keyframes(frame_paths: list[Path], params: LearnedRuntimeParams) -> list[SelectedFrame]:
    if not frame_paths:
        raise LearnedRuntimeError("No extracted frame images were found for learned runtime.")
    selected = [
        SelectedFrame(source_index=index, source_path=path)
        for index, path in enumerate(frame_paths)
        if index % params.frame_step == 0
    ][: params.max_frames]
    if not selected:
        raise LearnedRuntimeError("Learned runtime frame selection produced no frames.")
    return selected


def preflight_learned_runtime(
    *,
    config: LearnedRuntimeConfig,
    params: LearnedRuntimeParams,
    frame_paths: list[Path],
) -> LearnedRuntimePreflight:
    selected = select_keyframes(frame_paths, params)
    command_check = _command_dependency(config.command)
    torch_info = _probe_torch(config.python_path)
    gpu_info = _probe_gpu()
    checkpoint_info = _inspect_checkpoint(config)
    budget = _estimate_runtime_budget(config, params, selected, checkpoint_info, gpu_info)
    dependencies = [command_check]
    blockers: list[str] = []
    warnings = [
        "Learned runtime output is predicted geometry and must be inspected before treating it as useful reconstruction evidence.",
        "No model or checkpoint is downloaded automatically by RoomSplat.",
    ]
    next_steps: list[str] = []
    status: LearnedRuntimeStatus = "ready"

    if not command_check.available:
        status = "blocked_missing_dependencies"
        blockers.append("learned runtime command is not configured or was not found")
        next_steps.append("Set ROOMSPLAT_LEARNED_RUNTIME_COMMAND to a local adapter executable or script wrapper.")
    if not torch_info.get("available"):
        warnings.append("PyTorch CUDA readiness could not be confirmed; the runtime command may still manage its own environment.")
        next_steps.append("Set ROOMSPLAT_LEARNED_RUNTIME_PYTHON_PATH to the runtime environment's python.exe for better diagnostics.")
    if checkpoint_info["status"] == "missing":
        status = _combine_status(status, "blocked_missing_checkpoint")
        blockers.append("learned runtime checkpoint is not configured or was not found")
        next_steps.append("Set ROOMSPLAT_LEARNED_CHECKPOINT_PATH to a checkpoint under ROOMSPLAT_LEARNED_MODEL_ROOT.")
    if checkpoint_info["status"] == "untrusted":
        status = _combine_status(status, "blocked_untrusted_checkpoint")
        blockers.append("learned runtime checkpoint hash is not allowlisted")
        next_steps.append("Set ROOMSPLAT_LEARNED_CHECKPOINT_SHA256 to the expected SHA-256 before running the adapter.")
    if not blockers and budget["vram_status"] == "insufficient":
        status = _combine_status(status, "blocked_insufficient_vram")
        blockers.append("estimated free VRAM is below the configured learned runtime budget")
        next_steps.append("Reduce max_frames or image_max_size, switch to fp16, or enable CPU/offload in the selected runtime.")

    summary = "Learned runtime is ready for a small local smoke run." if status == "ready" else "Learned runtime is blocked; no geometry will be generated."
    return LearnedRuntimePreflight(
        adapter=params.adapter,
        status=status,
        summary=summary,
        dependencies=dependencies,
        blockers=blockers,
        warnings=warnings,
        next_steps=next_steps,
        gpu=gpu_info,
        torch=torch_info,
        checkpoint=checkpoint_info,
        runtime_budget=budget,
        selected_frame_indices=[frame.source_index for frame in selected],
        expected_outputs=[
            {
                "name": artifact.name,
                "path": artifact.path.as_posix(),
                "artifact_type": artifact.artifact_type,
                "description": artifact.description,
            }
            for artifact in learned_geometry_expected_outputs()
        ],
        generated_data_rules=_generated_data_rules(config),
    )


def run_learned_runtime_command(
    *,
    config: LearnedRuntimeConfig,
    params: LearnedRuntimeParams,
    selected_frames_dir: Path,
    output_dir: Path,
    source_indices: list[int],
) -> dict[str, Any]:
    if not config.command:
        raise LearnedRuntimeError("learned runtime command is not configured.")
    checkpoint = config.checkpoint_path
    if not checkpoint:
        raise LearnedRuntimeError("learned runtime checkpoint is not configured.")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [
        config.command,
        *_split_args(config.args),
        "--frames-dir",
        str(selected_frames_dir),
        "--output-dir",
        str(output_dir),
        "--checkpoint",
        str(_resolve_checkpoint_path(config)),
        "--max-frames",
        str(params.max_frames),
        "--image-max-size",
        str(params.image_max_size),
        "--precision",
        params.precision,
        "--frame-index-map",
        ",".join(str(index) for index in source_indices),
    ]
    if params.allow_cpu_offload:
        command.append("--allow-cpu-offload")
    completed = subprocess.run(
        command,
        cwd=str(output_dir),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=config.timeout_seconds,
        check=False,
    )
    return {
        "command": _redact_command(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def materialize_selected_frames(selected: list[SelectedFrame], destination_dir: Path) -> list[dict[str, Any]]:
    destination_dir.mkdir(parents=True, exist_ok=True)
    materialized = []
    for output_index, frame in enumerate(selected):
        suffix = frame.source_path.suffix.lower()
        destination = destination_dir / f"frame_{output_index:06d}{suffix}"
        shutil.copyfile(frame.source_path, destination)
        materialized.append(
            {
                "bundle_frame_index": output_index,
                "source_frame_index": frame.source_index,
                "runtime_frame": destination.name,
                "source_frame_name": frame.source_path.name,
            }
        )
    return materialized


def _inspect_checkpoint(config: LearnedRuntimeConfig) -> dict[str, Any]:
    try:
        path = _resolve_checkpoint_path(config)
    except LearnedRuntimeError as exc:
        return {
            "status": "missing",
            "path": config.checkpoint_path,
            "model_root": str(config.model_root),
            "size_bytes": None,
            "sha256": None,
            "detail": str(exc),
        }
    digest = _sha256(path)
    expected = _normalize_hash(config.checkpoint_sha256)
    trusted = bool(expected and digest == expected)
    return {
        "status": "trusted" if trusted else "untrusted",
        "path": str(path),
        "model_root": str(config.model_root.resolve()),
        "size_bytes": path.stat().st_size,
        "sha256": digest,
        "expected_sha256": expected,
        "detail": "checkpoint hash matched allowlist" if trusted else "checkpoint exists, but SHA-256 was not allowlisted",
    }


def _resolve_checkpoint_path(config: LearnedRuntimeConfig) -> Path:
    if not config.checkpoint_path:
        raise LearnedRuntimeError("ROOMSPLAT_LEARNED_CHECKPOINT_PATH is not set.")
    model_root = config.model_root.expanduser().resolve()
    candidate = Path(config.checkpoint_path).expanduser()
    if not candidate.is_absolute():
        candidate = model_root / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(model_root)
    except ValueError as exc:
        raise LearnedRuntimeError("Checkpoint path must stay under ROOMSPLAT_LEARNED_MODEL_ROOT / model_root.") from exc
    if not resolved.is_file():
        raise LearnedRuntimeError("Configured checkpoint file was not found.")
    return resolved


def _estimate_runtime_budget(
    config: LearnedRuntimeConfig,
    params: LearnedRuntimeParams,
    selected: list[SelectedFrame],
    checkpoint: dict[str, Any],
    gpu: dict[str, Any],
) -> dict[str, Any]:
    checkpoint_mb = (checkpoint.get("size_bytes") or 0) / (1024 * 1024)
    precision_factor = {"fp32": 1.0, "fp16": 0.58, "bfloat16": 0.62}[params.precision]
    image_factor = (params.image_max_size / 768) ** 2
    estimated_mb = int(1800 + checkpoint_mb * 1.6 * precision_factor + len(selected) * 220 * image_factor * precision_factor)
    free_mb = gpu.get("memory_free_mb")
    vram_status = "unknown"
    if isinstance(free_mb, int):
        required_mb = max(config.min_free_vram_mb, estimated_mb)
        vram_status = "ok" if free_mb >= required_mb else "insufficient"
    return {
        "selected_frame_count": len(selected),
        "max_frames": params.max_frames,
        "frame_step": params.frame_step,
        "image_max_size": params.image_max_size,
        "precision": params.precision,
        "allow_cpu_offload": params.allow_cpu_offload,
        "estimated_required_vram_mb": estimated_mb,
        "min_free_vram_mb": config.min_free_vram_mb,
        "observed_free_vram_mb": free_mb,
        "vram_status": vram_status,
        "notes": "Estimate is conservative and includes checkpoint, activations, frames, and CUDA/PyTorch overhead.",
    }


def _probe_gpu() -> dict[str, Any]:
    executable = shutil.which("nvidia-smi")
    if not executable:
        return {"available": False, "detail": "nvidia-smi was not found on PATH."}
    completed = subprocess.run(
        [
            executable,
            "--query-gpu=name,memory.total,memory.free",
            "--format=csv,noheader,nounits",
        ],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
    if completed.returncode != 0:
        return {"available": False, "detail": completed.stderr.strip() or "nvidia-smi failed."}
    first_line = completed.stdout.splitlines()[0] if completed.stdout.splitlines() else ""
    parts = [part.strip() for part in first_line.split(",")]
    if len(parts) < 3:
        return {"available": False, "detail": "nvidia-smi returned an unexpected format."}
    return {
        "available": True,
        "name": parts[0],
        "memory_total_mb": _maybe_int(parts[1]),
        "memory_free_mb": _maybe_int(parts[2]),
        "detail": first_line,
    }


def _probe_torch(python_path: str | None) -> dict[str, Any]:
    python = python_path or sys.executable
    script = (
        "import json\n"
        "try:\n"
        " import torch\n"
        " print(json.dumps({'available': True, 'version': torch.__version__, 'cuda_available': torch.cuda.is_available(), "
        "'cuda_version': getattr(torch.version, 'cuda', None), 'device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}))\n"
        "except Exception as exc:\n"
        " print(json.dumps({'available': False, 'error': str(exc)}))\n"
    )
    try:
        completed = subprocess.run([python, "-c", script], capture_output=True, encoding="utf-8", errors="replace", timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "python": python, "error": str(exc)}
    try:
        payload = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        payload = {"available": False, "error": completed.stderr.strip() or completed.stdout.strip()}
    payload["python"] = python
    return payload


def _command_dependency(command: str | None) -> DependencyCheck:
    if not command:
        return DependencyCheck(
            name="learned_runtime_command",
            available=False,
            kind="executable",
            detail="Set ROOMSPLAT_LEARNED_RUNTIME_COMMAND to a local adapter executable.",
        )
    if Path(command).is_file() or shutil.which(command):
        return DependencyCheck(name="learned_runtime_command", available=True, kind="executable", detail=command)
    return DependencyCheck(name="learned_runtime_command", available=False, kind="executable", detail=f"Command not found: {command}")


def _combine_status(current: LearnedRuntimeStatus, candidate: LearnedRuntimeStatus) -> LearnedRuntimeStatus:
    priority = {
        "ready": 0,
        "blocked_missing_dependencies": 1,
        "blocked_missing_checkpoint": 2,
        "blocked_untrusted_checkpoint": 3,
        "blocked_insufficient_vram": 4,
    }
    return candidate if priority[candidate] > priority[current] else current


def _generated_data_rules(config: LearnedRuntimeConfig) -> dict[str, Any]:
    return {
        "local_only": True,
        "no_auto_downloads": True,
        "user_supplied_checkpoints_only": True,
        "checkpoint_under_model_root": True,
        "cache_dir": str(config.cache_dir),
        "ignored_by_git": True,
        "notes": "Learned runtime checkpoints, caches, and generated outputs must stay in ignored local data folders.",
    }


def _split_args(value: str | None) -> list[str]:
    if not value:
        return []
    return shlex.split(value, posix=False)


def _redact_command(command: list[str]) -> list[str]:
    redacted = list(command)
    for index, value in enumerate(redacted[:-1]):
        if value == "--checkpoint":
            redacted[index + 1] = "<checkpoint>"
    return redacted


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_hash(value: str | None) -> str | None:
    clean = str(value or "").strip().lower()
    if not clean:
        return None
    if len(clean) != 64 or any(character not in "0123456789abcdef" for character in clean):
        return None
    return clean


def _read_int(value: Any, field_name: str, *, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise LearnedRuntimeError(f"{field_name} must be an integer.") from exc
    if parsed < minimum or parsed > maximum:
        raise LearnedRuntimeError(f"{field_name} must be between {minimum} and {maximum}.")
    return parsed


def _maybe_int(value: str) -> int | None:
    try:
        return int(float(value))
    except ValueError:
        return None
