from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.services.frame_extraction import FrameExtractionError, inspect_video_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect deterministic local video fixtures.")
    parser.add_argument("--video", required=True, type=Path, help="Source video path. GIF fixtures are supported without ffmpeg.")
    args = parser.parse_args()

    try:
        metadata = inspect_video_file(args.video)
    except FrameExtractionError as exc:
        parser.exit(2, f"error: {exc}\n")

    print(json.dumps(metadata.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
