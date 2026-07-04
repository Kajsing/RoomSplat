import json
import subprocess
import sys
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.services.frame_extraction import extract_frames_from_file, inspect_video_file


def test_extract_frames_from_tiny_synthetic_media(tmp_path) -> None:
    video_path = tmp_path / "tiny.gif"
    frames_dir = tmp_path / "frames"
    video_path.write_bytes(_tiny_gif_bytes(frame_count=4))

    metadata = extract_frames_from_file(video_path, frames_dir, stride=2)

    assert metadata.fps == 10.0
    assert metadata.frame_count == 4
    assert metadata.extracted_frame_count == 2
    assert metadata.extraction_stride == 2
    assert metadata.width == 8
    assert metadata.height == 6
    assert (frames_dir / "frame_000001.png").is_file()
    assert (frames_dir / "frame_000002.png").is_file()


def test_inspect_video_script_reports_fixture_metadata(tmp_path) -> None:
    video_path = tmp_path / "tiny.gif"
    video_path.write_bytes(_tiny_gif_bytes(frame_count=3))

    result = subprocess.run(
        [
            sys.executable,
            str(Path("pipeline/scripts/inspect_video.py")),
            "--video",
            str(video_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    metadata = json.loads(result.stdout)
    assert metadata["frame_count"] == 3
    assert metadata["width"] == 8
    assert metadata["height"] == 6


def test_extract_frames_script_writes_frames(tmp_path) -> None:
    video_path = tmp_path / "tiny.gif"
    frames_dir = tmp_path / "script-frames"
    video_path.write_bytes(_tiny_gif_bytes(frame_count=5))

    result = subprocess.run(
        [
            sys.executable,
            str(Path("pipeline/scripts/extract_frames.py")),
            "--video",
            str(video_path),
            "--output",
            str(frames_dir),
            "--stride",
            "2",
            "--max-frames",
            "2",
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    metadata = json.loads(result.stdout)
    assert metadata["extracted_frame_count"] == 2
    assert (frames_dir / "frame_000001.png").is_file()
    assert (frames_dir / "frame_000002.png").is_file()


def test_inspect_video_file_reports_fixture_metadata(tmp_path) -> None:
    video_path = tmp_path / "tiny.gif"
    video_path.write_bytes(_tiny_gif_bytes(frame_count=2))

    metadata = inspect_video_file(video_path)

    assert metadata.frame_count == 2
    assert metadata.extracted_frame_count == 0


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
