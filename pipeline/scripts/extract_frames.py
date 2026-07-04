from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.frame_extraction import FrameExtractionError, extract_frames_from_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract deterministic frames from a tiny local video fixture.")
    parser.add_argument("--video", required=True, type=Path, help="Source video path. GIF fixtures are supported without ffmpeg.")
    parser.add_argument("--output", required=True, type=Path, help="Directory where extracted frames will be written.")
    parser.add_argument("--stride", default=1, type=int, help="Extract every Nth frame.")
    parser.add_argument("--max-frames", default=None, type=int, help="Optional maximum number of frames to write.")
    args = parser.parse_args()

    try:
        metadata = extract_frames_from_file(args.video, args.output, args.stride, args.max_frames)
    except FrameExtractionError as exc:
        parser.exit(2, f"error: {exc}\n")

    print(json.dumps(metadata.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
