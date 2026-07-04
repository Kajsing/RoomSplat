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
    max_upload_bytes: int = 2 * 1024 * 1024 * 1024
    ffmpeg_timeout_seconds: int = 30 * 60


def get_config() -> AppConfig:
    data_dir = Path(os.environ.get("ROOMSPLAT_DATA_DIR") or os.environ.get("DATA_DIR", "data"))
    ffmpeg_path = os.environ.get("ROOMSPLAT_FFMPEG_PATH") or os.environ.get("FFMPEG_PATH")
    colmap_path = os.environ.get("ROOMSPLAT_COLMAP_PATH") or os.environ.get("COLMAP_PATH")
    nerfstudio_bin_dir = os.environ.get("ROOMSPLAT_NERFSTUDIO_BIN_DIR")
    ns_process_data_path = os.environ.get("ROOMSPLAT_NS_PROCESS_DATA_PATH")
    ns_train_path = os.environ.get("ROOMSPLAT_NS_TRAIN_PATH")
    ns_export_path = os.environ.get("ROOMSPLAT_NS_EXPORT_PATH")
    max_upload_mb = os.environ.get("ROOMSPLAT_MAX_UPLOAD_MB") or os.environ.get("MAX_UPLOAD_MB")
    max_upload_bytes = int(max_upload_mb) * 1024 * 1024 if max_upload_mb else AppConfig().max_upload_bytes
    timeout_seconds = int(os.environ.get("ROOMSPLAT_FFMPEG_TIMEOUT_SECONDS", AppConfig().ffmpeg_timeout_seconds))
    return AppConfig(
        data_dir=data_dir,
        ffmpeg_path=ffmpeg_path,
        colmap_path=colmap_path,
        nerfstudio_bin_dir=nerfstudio_bin_dir,
        ns_process_data_path=ns_process_data_path,
        ns_train_path=ns_train_path,
        ns_export_path=ns_export_path,
        max_upload_bytes=max_upload_bytes,
        ffmpeg_timeout_seconds=timeout_seconds,
    )
