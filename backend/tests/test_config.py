from app.config import get_config


def test_get_config_reads_local_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(
        "\n".join(
            [
                "ROOMSPLAT_DATA_DIR=C:\\project\\RoomSplat\\data",
                "ROOMSPLAT_FFMPEG_PATH=C:\\tools\\ffmpeg.exe",
                "ROOMSPLAT_COLMAP_PATH=C:\\tools\\colmap.exe",
                "ROOMSPLAT_MAX_UPLOAD_MB=16",
                "ROOMSPLAT_FFMPEG_TIMEOUT_SECONDS=42",
                "",
            ]
        ),
        encoding="utf-8",
    )

    config = get_config()

    assert str(config.data_dir) == "C:\\project\\RoomSplat\\data"
    assert config.ffmpeg_path == "C:\\tools\\ffmpeg.exe"
    assert config.colmap_path == "C:\\tools\\colmap.exe"
    assert config.max_upload_bytes == 16 * 1024 * 1024
    assert config.ffmpeg_timeout_seconds == 42


def test_environment_variables_override_local_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("ROOMSPLAT_DATA_DIR=C:\\from-env-file\n", encoding="utf-8")
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", "C:\\from-process-env")

    config = get_config()

    assert str(config.data_dir) == "C:\\from-process-env"
