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
