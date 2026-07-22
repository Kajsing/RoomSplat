import os
from pathlib import Path

from pydantic import BaseModel


class AppConfig(BaseModel):
    app_name: str = "local-3d-room-mapper"
    version: str = "0.1.0"
    data_dir: Path = Path("data")
    ffmpeg_path: str | None = None
    colmap_path: str | None = None
    nerfstudio_bin_dir: str | None = None
    ns_process_data_path: str | None = None
    ns_train_path: str | None = None
    ns_export_path: str | None = None
    nerfstudio_python_path: str | None = None
    learned_runtime_command: str | None = None
    learned_runtime_args: str | None = None
    learned_runtime_python_path: str | None = None
    learned_checkpoint_path: str | None = None
    learned_checkpoint_sha256: str | None = None
    learned_model_root: Path = Path("data") / "models"
    learned_cache_dir: Path = Path("data") / "cache" / "learned-runtime"
    learned_min_free_vram_mb: int = 10_000
    learned_runtime_timeout_seconds: int = 30 * 60
    max_upload_bytes: int = 2 * 1024 * 1024 * 1024
    ffmpeg_timeout_seconds: int = 30 * 60


def get_config() -> AppConfig:
    env_file = _read_env_file(Path(".env"))

    def env_value(*names: str) -> str | None:
        for name in names:
            value = os.environ.get(name)
            if value:
                return value
        for name in names:
            value = env_file.get(name)
            if value:
                return value
        return None

    data_dir = Path(env_value("ROOMSPLAT_DATA_DIR", "DATA_DIR") or "data")
    ffmpeg_path = env_value("ROOMSPLAT_FFMPEG_PATH", "FFMPEG_PATH")
    colmap_path = env_value("ROOMSPLAT_COLMAP_PATH", "COLMAP_PATH")
    nerfstudio_bin_dir = env_value("ROOMSPLAT_NERFSTUDIO_BIN_DIR")
    ns_process_data_path = env_value("ROOMSPLAT_NS_PROCESS_DATA_PATH")
    ns_train_path = env_value("ROOMSPLAT_NS_TRAIN_PATH")
    ns_export_path = env_value("ROOMSPLAT_NS_EXPORT_PATH")
    nerfstudio_python_path = env_value("ROOMSPLAT_NERFSTUDIO_PYTHON_PATH")
    learned_runtime_command = env_value("ROOMSPLAT_LEARNED_RUNTIME_COMMAND")
    learned_runtime_args = env_value("ROOMSPLAT_LEARNED_RUNTIME_ARGS")
    learned_runtime_python_path = env_value("ROOMSPLAT_LEARNED_RUNTIME_PYTHON_PATH")
    learned_checkpoint_path = env_value("ROOMSPLAT_LEARNED_CHECKPOINT_PATH")
    learned_checkpoint_sha256 = env_value("ROOMSPLAT_LEARNED_CHECKPOINT_SHA256")
    learned_model_root = Path(env_value("ROOMSPLAT_LEARNED_MODEL_ROOT") or AppConfig().learned_model_root)
    learned_cache_dir = Path(env_value("ROOMSPLAT_LEARNED_CACHE_DIR") or AppConfig().learned_cache_dir)
    learned_min_free_vram_mb = int(env_value("ROOMSPLAT_LEARNED_MIN_FREE_VRAM_MB") or AppConfig().learned_min_free_vram_mb)
    learned_runtime_timeout_seconds = int(
        env_value("ROOMSPLAT_LEARNED_RUNTIME_TIMEOUT_SECONDS") or AppConfig().learned_runtime_timeout_seconds
    )
    max_upload_mb = env_value("ROOMSPLAT_MAX_UPLOAD_MB", "MAX_UPLOAD_MB")
    max_upload_bytes = int(max_upload_mb) * 1024 * 1024 if max_upload_mb else AppConfig().max_upload_bytes
    timeout_seconds = int(env_value("ROOMSPLAT_FFMPEG_TIMEOUT_SECONDS") or AppConfig().ffmpeg_timeout_seconds)
    return AppConfig(
        data_dir=data_dir,
        ffmpeg_path=ffmpeg_path,
        colmap_path=colmap_path,
        nerfstudio_bin_dir=nerfstudio_bin_dir,
        ns_process_data_path=ns_process_data_path,
        ns_train_path=ns_train_path,
        ns_export_path=ns_export_path,
        nerfstudio_python_path=nerfstudio_python_path,
        learned_runtime_command=learned_runtime_command,
        learned_runtime_args=learned_runtime_args,
        learned_runtime_python_path=learned_runtime_python_path,
        learned_checkpoint_path=learned_checkpoint_path,
        learned_checkpoint_sha256=learned_checkpoint_sha256,
        learned_model_root=learned_model_root,
        learned_cache_dir=learned_cache_dir,
        learned_min_free_vram_mb=learned_min_free_vram_mb,
        learned_runtime_timeout_seconds=learned_runtime_timeout_seconds,
        max_upload_bytes=max_upload_bytes,
        ffmpeg_timeout_seconds=timeout_seconds,
    )


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values
