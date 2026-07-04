
from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image, ImageSequence

from app.models.schemas import FrameExtractionResponse
from app.services.project_store import ProjectStore, ProjectStoreError


class FrameExtractionError(ValueError):
    pass


class FrameExtractionService:
    def __init__(self, project_store: ProjectStore, ffmpeg_path: str | None = None) -> None:
        self.project_store = project_store
        self.ffmpeg_path = ffmpeg_path

    def extract_frames(
        self,
        project_id: str,
        source_video: str | None = None,
        stride: int = 1,
        max_frames: int | None = None,
    ) -> FrameExtractionResponse:
        if stride < 1:
            raise FrameExtractionError("Frame extraction stride must be at least 1.")
        if max_frames is not None and max_frames < 1:
            raise FrameExtractionError("max_frames must be at least 1 when provided.")

        try:
            project_dir = self.project_store.get_project_dir(project_id)
        except ProjectStoreError as exc:
            raise FrameExtractionError(str(exc)) from exc

        source_path = self._resolve_source_video(project_dir, source_video)
        frames_dir = (project_dir / "frames").resolve()
        _ensure_inside_project(frames_dir, project_dir)
        frames_dir.mkdir(exist_ok=True)
        _clear_existing_frames(frames_dir)

        if source_path.suffix.lower() == ".gif":
            response = _extract_gif_frames(project_id, source_path, frames_dir, stride, max_frames)
        else:
            response = self._extract_with_ffmpeg(project_id, source_path, frames_dir, stride, max_frames)

        metadata_path = (project_dir / "metadata" / "frame_extraction.json").resolve()
        _ensure_inside_project(metadata_path, project_dir)
        metadata_path.write_text(json.dumps(response.model_dump(), indent=2) + "\n", encoding="utf-8")
        return response

    def inspect_video(self, project_id: str, source_video: str | None = None) -> FrameExtractionResponse:
        try:
            project_dir = self.project_store.get_project_dir(project_id)
        except ProjectStoreError as exc:
            raise FrameExtractionError(str(exc)) from exc

        source_path = self._resolve_source_video(project_dir, source_video)
        frames_dir = (project_dir / "frames").resolve()
        if source_path.suffix.lower() == ".gif":
            return _inspect_gif(project_id, source_path, frames_dir)
        raise FrameExtractionError("Inspection for this video type requires extraction with ffmpeg.")

    def _resolve_source_video(self, project_dir: Path, source_video: str | None) -> Path:
        if source_video:
            source_path = Path(source_video).resolve()
        else:
            metadata_path = project_dir / "metadata" / "video_import.json"
            if not metadata_path.exists():
                raise FrameExtractionError("No imported video was found for this project.")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            source_path = Path(metadata["source_video"]).resolve()

        _ensure_inside_project(source_path, project_dir)
        if not source_path.is_file():
            raise FrameExtractionError("Source video was not found.")
        return source_path

    def _extract_with_ffmpeg(
        self,
        project_id: str,
        source_path: Path,
        frames_dir: Path,
        stride: int,
        max_frames: int | None,
    ) -> FrameExtractionResponse:
        ffmpeg = self.ffmpeg_path or shutil.which("ffmpeg")
        if not ffmpeg:
            raise FrameExtractionError(
                "ffmpeg is required to extract frames from this video type. "
                "Install ffmpeg and add it to PATH, or set ROOMSPLAT_FFMPEG_PATH."
            )

        output_pattern = str(frames_dir / "frame_%06d.png")
        vf = f"select='not(mod(n\\,{stride}))'"
        command = [
            ffmpeg,
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source_path),
            "-vf",
            vf,
            "-vsync",
            "vfr",
        ]
        if max_frames is not None:
            command.extend(["-frames:v", str(max_frames)])
        command.append(output_pattern)

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise FrameExtractionError(result.stderr.strip() or "ffmpeg frame extraction failed.")

        frame_paths = sorted(frames_dir.glob("frame_*.png"))
        if not frame_paths:
            raise FrameExtractionError("ffmpeg did not produce any frames.")

        width, height = _image_size(frame_paths[0])
        return FrameExtractionResponse(
            project_id=project_id,
            source_video=str(source_path),
            frames_dir=str(frames_dir),
            fps=0.0,
            frame_count=len(frame_paths) * stride,
            extracted_frame_count=len(frame_paths),
            extraction_stride=stride,
            width=width,
            height=height,
            extracted_at=datetime.now(UTC).isoformat(),
        )


def extract_frames_from_file(
    source_video: Path,
    frames_dir: Path,
    stride: int = 1,
    max_frames: int | None = None,
) -> FrameExtractionResponse:
    source_path = source_video.resolve()
    output_dir = frames_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    _clear_existing_frames(output_dir)
    if source_path.suffix.lower() != ".gif":
        raise FrameExtractionError("The standalone extractor currently supports deterministic GIF media.")
    return _extract_gif_frames("standalone", source_path, output_dir, stride, max_frames)


def inspect_video_file(source_video: Path, frames_dir: Path | None = None) -> FrameExtractionResponse:
    source_path = source_video.resolve()
    output_dir = frames_dir.resolve() if frames_dir else source_path.parent.resolve()
    if source_path.suffix.lower() != ".gif":
        raise FrameExtractionError("The standalone inspector currently supports deterministic GIF media.")
    return _inspect_gif("standalone", source_path, output_dir)


def _extract_gif_frames(
    project_id: str,
    source_path: Path,
    frames_dir: Path,
    stride: int,
    max_frames: int | None,
) -> FrameExtractionResponse:
    with Image.open(source_path) as image:
        width, height = image.size
        frame_count = getattr(image, "n_frames", 1)
        fps = _gif_fps(image)
        extracted = 0
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            if index % stride != 0:
                continue
            if max_frames is not None and extracted >= max_frames:
                break
            output_path = frames_dir / f"frame_{extracted + 1:06d}.png"
            frame.convert("RGB").save(output_path)
            extracted += 1

    if extracted == 0:
        raise FrameExtractionError("Frame extraction did not produce any frames.")

    return FrameExtractionResponse(
        project_id=project_id,
        source_video=str(source_path),
        frames_dir=str(frames_dir),
        fps=fps,
        frame_count=frame_count,
        extracted_frame_count=extracted,
        extraction_stride=stride,
        width=width,
        height=height,
        extracted_at=datetime.now(UTC).isoformat(),
    )


def _inspect_gif(project_id: str, source_path: Path, frames_dir: Path) -> FrameExtractionResponse:
    with Image.open(source_path) as image:
        width, height = image.size
        frame_count = getattr(image, "n_frames", 1)
        fps = _gif_fps(image)
    return FrameExtractionResponse(
        project_id=project_id,
        source_video=str(source_path),
        frames_dir=str(frames_dir),
        fps=fps,
        frame_count=frame_count,
        extracted_frame_count=0,
        extraction_stride=1,
        width=width,
        height=height,
        extracted_at=datetime.now(UTC).isoformat(),
    )


def _gif_fps(image: Image.Image) -> float:
    duration_ms = float(image.info.get("duration") or 100)
    return 1000.0 / duration_ms if duration_ms > 0 else 10.0


def _clear_existing_frames(frames_dir: Path) -> None:
    for path in frames_dir.glob("frame_*.png"):
        if path.is_file():
            path.unlink()


def _image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def _ensure_inside_project(path: Path, project_dir: Path) -> None:
    try:
        path.resolve().relative_to(project_dir.resolve())
    except ValueError as exc:
        raise FrameExtractionError("Frame extraction path escaped the project directory.") from exc
