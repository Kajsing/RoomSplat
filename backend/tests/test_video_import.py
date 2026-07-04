import json
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


def test_upload_video_copies_file_and_records_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Video import"}).json()
    video_bytes = _tiny_gif_bytes(frame_count=3)

    response = client.post(
        f"/projects/{project['id']}/videos/upload",
        params={"filename": "room scan.gif"},
        content=video_bytes,
        headers={"content-type": "image/gif"},
    )

    assert response.status_code == 201
    imported = response.json()
    source_path = tmp_path / project["id"] / "input" / imported["stored_filename"]
    metadata_path = tmp_path / project["id"] / "metadata" / "video_import.json"

    assert source_path.read_bytes() == video_bytes
    assert imported["original_filename"] == "room scan.gif"
    assert imported["size_bytes"] == len(video_bytes)
    assert json.loads(metadata_path.read_text(encoding="utf-8")) == imported


def test_extract_frames_from_uploaded_video_records_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Frame extraction"}).json()
    client.post(
        f"/projects/{project['id']}/videos/upload",
        params={"filename": "tiny.gif"},
        content=_tiny_gif_bytes(frame_count=5),
        headers={"content-type": "image/gif"},
    )

    response = client.post(
        f"/projects/{project['id']}/frames/extract",
        json={"stride": 2, "max_frames": 2},
    )

    assert response.status_code == 200
    metadata = response.json()
    frames_dir = tmp_path / project["id"] / "frames"
    metadata_path = tmp_path / project["id"] / "metadata" / "frame_extraction.json"

    assert metadata["fps"] == 10.0
    assert metadata["frame_count"] == 5
    assert metadata["extracted_frame_count"] == 2
    assert metadata["extraction_stride"] == 2
    assert metadata["width"] == 8
    assert metadata["height"] == 6
    assert (frames_dir / "frame_000001.png").is_file()
    assert (frames_dir / "frame_000002.png").is_file()
    assert json.loads(metadata_path.read_text(encoding="utf-8")) == metadata


def test_upload_rejects_unsupported_extension(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Reject invalid"}).json()

    response = client.post(
        f"/projects/{project['id']}/videos/upload",
        params={"filename": "notes.txt"},
        content=b"not a video",
    )

    assert response.status_code == 400


def _tiny_gif_bytes(frame_count: int) -> bytes:
    frames = []
    for index in range(frame_count):
        frame = Image.new("RGB", (8, 6), (index * 30, index * 20, index * 10))
        frames.append(frame)

    output = BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=100,
        loop=0,
    )
    return output.getvalue()
