# Pipeline

Milestone 3 supports deterministic frame extraction for tiny animated GIF fixtures without external binaries. This keeps tests small and reproducible on Windows.

General video formats such as `.mp4`, `.mov`, `.avi`, `.mkv`, and `.webm` are accepted by the app upload path. Extracting frames from those formats requires `ffmpeg` on `PATH` or `ROOMSPLAT_FFMPEG_PATH` / `FFMPEG_PATH` set to the executable path.

## Inspect a tiny fixture

```bash
python pipeline/scripts/inspect_video.py --video path/to/tiny.gif
```

## Extract frames

```bash
python pipeline/scripts/extract_frames.py --video path/to/tiny.gif --output data/tmp-frames --stride 2 --max-frames 10
```

Frames are written as `frame_000001.png`, `frame_000002.png`, and so on. Metadata is printed as JSON by the CLI and written under project `metadata/` by the backend API.
