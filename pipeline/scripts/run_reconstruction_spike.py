from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pipeline.adapters import (
    ColmapPoseAdapter,
    GsplatResearchAdapter,
    NerfstudioSplatfactoAdapter,
    Open3DDebugAdapter,
    ReconstructionInput,
)


SUPPORTED_FRAME_EXTENSIONS = {".png", ".jpg", ".jpeg"}
PRIMARY_INTERIM_PATH = "COLMAP or pycolmap poses -> Nerfstudio Splatfacto -> splat.ply"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate local reconstruction readiness without running expensive training. "
            "The spike validates extracted frames, checks adapter dependencies, and reports "
            "the recommended interim Gaussian Splatting path."
        )
    )
    parser.add_argument("--project", type=Path, help="Project folder containing a frames/ directory.")
    parser.add_argument("--frames-dir", type=Path, help="Extracted frames directory. Overrides --project frames/.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write metadata/reconstruction_spike.json when --project is provided.",
    )
    args = parser.parse_args()

    try:
        project_dir = args.project.resolve() if args.project else None
        frames_dir = resolve_frames_dir(project_dir, args.frames_dir)
        reconstruction_input = inspect_frames(frames_dir)
        report = build_report(reconstruction_input, project_dir)
        if args.write_report:
            if project_dir is None:
                parser.error("--write-report requires --project.")
            write_report(project_dir, report)
    except SpikeError as exc:
        parser.exit(2, f"error: {exc}\n")

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_human_report(report)
    return 0


def resolve_frames_dir(project_dir: Path | None, frames_dir: Path | None) -> Path:
    if frames_dir is not None:
        return frames_dir.resolve()
    if project_dir is not None:
        return (project_dir / "frames").resolve()
    raise SpikeError("Provide --project or --frames-dir.")


def inspect_frames(frames_dir: Path) -> ReconstructionInput:
    if not frames_dir.is_dir():
        raise SpikeError(f"Frames directory does not exist: {frames_dir}")

    frames = sorted(path for path in frames_dir.iterdir() if path.suffix.lower() in SUPPORTED_FRAME_EXTENSIONS)
    if not frames:
        raise SpikeError(f"No frame images found in: {frames_dir}")

    with Image.open(frames[0]) as image:
        width, height = image.size

    return ReconstructionInput(
        frames_dir=frames_dir,
        frame_count=len(frames),
        width=width,
        height=height,
    )


def build_report(reconstruction_input: ReconstructionInput, project_dir: Path | None = None) -> dict[str, Any]:
    adapters = [
        ColmapPoseAdapter(),
        NerfstudioSplatfactoAdapter(),
        GsplatResearchAdapter(),
        Open3DDebugAdapter(),
    ]
    assessments = [adapter.assess(reconstruction_input) for adapter in adapters]
    ready_adapters = [assessment.adapter for assessment in assessments if assessment.is_ready]
    has_full_interim_path = "colmap" in ready_adapters and "nerfstudio-splatfacto" in ready_adapters

    if reconstruction_input.frame_count < 3:
        status = "insufficient_input"
        guidance = "Capture or extract at least 3 overlapping frames before attempting reconstruction."
    elif has_full_interim_path:
        status = "ready_to_attempt_interim_path"
        guidance = "Local dependencies appear sufficient to attempt the interim Splatfacto path."
    else:
        status = "stop_condition_missing_dependencies"
        guidance = (
            "Frames are present, but local reconstruction dependencies are missing. "
            "Install COLMAP/pycolmap for poses and Nerfstudio/Splatfacto for the first splat path."
        )

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "status": status,
        "project_dir": str(project_dir) if project_dir else None,
        "selected_interim_path": PRIMARY_INTERIM_PATH,
        "guidance": guidance,
        "input": {
            "frames_dir": str(reconstruction_input.frames_dir),
            "frame_count": reconstruction_input.frame_count,
            "width": reconstruction_input.width,
            "height": reconstruction_input.height,
        },
        "adapters": [_to_jsonable(assessment) for assessment in assessments],
        "output_contract": [
            {
                "artifact": "reconstruction/cameras.json",
                "artifact_type": "camera_poses",
                "real_when": "COLMAP or pycolmap pose estimation succeeds.",
            },
            {
                "artifact": "reconstruction/pointcloud.ply",
                "artifact_type": "point_cloud_ply",
                "real_when": "Sparse SfM point cloud is exported; not a Gaussian splat.",
            },
            {
                "artifact": "reconstruction/splat.ply",
                "artifact_type": "splat_ply",
                "real_when": "Splatfacto, gsplat, or a future learned/generative splat adapter exports real Gaussian splats.",
            },
        ],
        "future_upgrade_seams": [
            "Keep backend jobs calling adapter names and artifact contracts, not tool-specific commands.",
            "Allow a later fast learned/generative splat adapter to consume frames or poses and emit the same splat_ply contract.",
            "Keep splat PLY, point-cloud PLY, and GLB labels distinct in metadata and UI.",
        ],
        "sources": [
            "https://docs.nerf.studio/quickstart/installation.html",
            "https://docs.nerf.studio/nerfology/methods/splat.html",
            "https://colmap.github.io/pycolmap/index.html",
            "https://github.com/nerfstudio-project/gsplat/blob/main/docs/INSTALL_WIN.md",
            "https://www.open3d.org/docs/release/getting_started.html",
        ],
    }


def write_report(project_dir: Path, report: dict[str, Any]) -> Path:
    metadata_dir = (project_dir / "metadata").resolve()
    metadata_dir.mkdir(exist_ok=True)
    report_path = metadata_dir / "reconstruction_spike.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report_path


def print_human_report(report: dict[str, Any]) -> None:
    print("RoomSplat reconstruction spike")
    print(f"Status: {report['status']}")
    print(f"Interim path: {report['selected_interim_path']}")
    print(f"Frames: {report['input']['frame_count']} at {report['input']['width']}x{report['input']['height']}")
    print(f"Guidance: {report['guidance']}")
    print("")
    print("Adapters:")
    for adapter in report["adapters"]:
        missing = [dep["name"] for dep in adapter["dependencies"] if not dep["available"]]
        suffix = f" missing: {', '.join(missing)}" if missing else " dependencies available"
        print(f"- {adapter['adapter']}: {adapter['status']};{suffix}")


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


class SpikeError(ValueError):
    pass


if __name__ == "__main__":
    raise SystemExit(main())
