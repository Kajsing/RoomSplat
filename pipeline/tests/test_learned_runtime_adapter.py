from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

import pipeline.adapters.learned_runtime as learned_runtime
from pipeline.adapters.learned_runtime import (
    LearnedRuntimeConfig,
    LearnedRuntimeError,
    build_learned_runtime_params,
    preflight_learned_runtime,
    select_keyframes,
)


def test_build_learned_runtime_params_validates_frame_budget() -> None:
    params = build_learned_runtime_params({"max_frames": "8", "frame_step": "2", "image_max_size": "512", "precision": "fp16"})

    assert params.max_frames == 8
    assert params.frame_step == 2
    assert params.image_max_size == 512

    with pytest.raises(LearnedRuntimeError, match="max_frames"):
        build_learned_runtime_params({"max_frames": 0})
    with pytest.raises(LearnedRuntimeError, match="precision"):
        build_learned_runtime_params({"precision": "int4"})


def test_select_keyframes_is_deterministic() -> None:
    frames = [Path(f"frame_{index:06d}.png") for index in range(10)]
    params = build_learned_runtime_params({"max_frames": 3, "frame_step": 2})

    selected = select_keyframes(frames, params)

    assert [frame.source_index for frame in selected] == [0, 2, 4]
    assert [frame.source_path.name for frame in selected] == ["frame_000000.png", "frame_000002.png", "frame_000004.png"]


def test_preflight_blocks_checkpoint_outside_model_root(tmp_path, monkeypatch) -> None:
    outside = tmp_path / "outside.pt"
    outside.write_bytes(b"checkpoint")
    config = LearnedRuntimeConfig(command=sys.executable, checkpoint_path=str(outside), model_root=tmp_path / "models")
    monkeypatch.setattr(learned_runtime, "_probe_gpu", lambda: {"available": True, "memory_free_mb": 12_000})
    monkeypatch.setattr(learned_runtime, "_probe_torch", lambda _python_path: {"available": True, "cuda_available": True})

    result = preflight_learned_runtime(config=config, params=build_learned_runtime_params(), frame_paths=[Path("a.png")])

    assert result.status == "blocked_missing_checkpoint"
    assert "model_root" in result.checkpoint["detail"]


def test_preflight_blocks_untrusted_checkpoint_until_hash_is_allowlisted(tmp_path, monkeypatch) -> None:
    model_root = tmp_path / "models"
    model_root.mkdir()
    checkpoint = model_root / "model.pt"
    checkpoint.write_bytes(b"trusted bytes")
    digest = hashlib.sha256(b"trusted bytes").hexdigest()
    monkeypatch.setattr(learned_runtime, "_probe_gpu", lambda: {"available": True, "memory_free_mb": 12_000})
    monkeypatch.setattr(learned_runtime, "_probe_torch", lambda _python_path: {"available": True, "cuda_available": True})

    untrusted = preflight_learned_runtime(
        config=LearnedRuntimeConfig(command=sys.executable, checkpoint_path="model.pt", model_root=model_root),
        params=build_learned_runtime_params({"max_frames": 1}),
        frame_paths=[Path("a.png")],
    )
    trusted = preflight_learned_runtime(
        config=LearnedRuntimeConfig(command=sys.executable, checkpoint_path="model.pt", checkpoint_sha256=digest, model_root=model_root),
        params=build_learned_runtime_params({"max_frames": 1}),
        frame_paths=[Path("a.png")],
    )

    assert untrusted.status == "blocked_untrusted_checkpoint"
    assert trusted.status == "ready"
    assert trusted.checkpoint["sha256"] == digest
    assert trusted.generated_data_rules["no_auto_downloads"] is True


def test_preflight_blocks_insufficient_vram(tmp_path, monkeypatch) -> None:
    model_root = tmp_path / "models"
    model_root.mkdir()
    checkpoint = model_root / "model.pt"
    checkpoint.write_bytes(b"tiny")
    digest = hashlib.sha256(b"tiny").hexdigest()
    monkeypatch.setattr(learned_runtime, "_probe_gpu", lambda: {"available": True, "memory_free_mb": 1_000})
    monkeypatch.setattr(learned_runtime, "_probe_torch", lambda _python_path: {"available": True, "cuda_available": True})

    result = preflight_learned_runtime(
        config=LearnedRuntimeConfig(
            command=sys.executable,
            checkpoint_path="model.pt",
            checkpoint_sha256=digest,
            model_root=model_root,
            min_free_vram_mb=8_000,
        ),
        params=build_learned_runtime_params({"max_frames": 4}),
        frame_paths=[Path(f"{index}.png") for index in range(8)],
    )

    assert result.status == "blocked_insufficient_vram"
    assert result.runtime_budget["vram_status"] == "insufficient"
