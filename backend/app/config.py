import os
from pathlib import Path

from pydantic import BaseModel


class AppConfig(BaseModel):
    app_name: str = "local-3d-room-mapper"
    version: str = "0.1.0"
    data_dir: Path = Path("data")


def get_config() -> AppConfig:
    data_dir = Path(os.environ.get("ROOMSPLAT_DATA_DIR") or os.environ.get("DATA_DIR", "data"))
    return AppConfig(data_dir=data_dir)
