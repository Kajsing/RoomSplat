from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence


class ColmapRunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class ColmapPaths:
    database_path: Path
    frames_dir: Path
    sparse_dir: Path
    sparse_model_dir: Path
    text_model_dir: Path
    output_ply: Path


@dataclass(frozen=True)
class ColmapCamera:
    camera_id: int
    model: str
    width: int
    height: int
    params: tuple[float, ...]


@dataclass(frozen=True)
class ColmapRegisteredImage:
    image_id: int
    camera_id: int
    name: str
    qvec: tuple[float, float, float, float]
    tvec: tuple[float, float, float]
    center: tuple[float, float, float]


@dataclass(frozen=True)
class ColmapTrajectoryBounds:
    min: tuple[float, float, float]
    max: tuple[float, float, float]


@dataclass(frozen=True)
class ColmapModelMetadata:
    cameras: tuple[ColmapCamera, ...]
    registered_images: tuple[ColmapRegisteredImage, ...]
    trajectory_bounds: ColmapTrajectoryBounds | None


@dataclass(frozen=True)
class ColmapRunResult:
    executable: str
    matcher: str
    use_gpu: bool
    workspace_dir: Path
    output_ply: Path
    registered_image_count: int
    sparse_point_count: int
    ply_point_count: int
    command_count: int
    model_metadata: ColmapModelMetadata | None = None


CommandRunner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class ColmapSparseReconstructionRunner:
    def __init__(self, executable: str | None = None, command_runner: CommandRunner | None = None) -> None:
        self.executable = resolve_colmap_executable(executable)
        self._command_runner = command_runner or self._run_subprocess

    def run(
        self,
        frames_dir: Path,
        workspace_dir: Path,
        output_ply: Path,
        *,
        matcher: str = "exhaustive",
        use_gpu: bool = False,
    ) -> ColmapRunResult:
        clean_matcher = validate_matcher(matcher)
        paths = build_colmap_paths(frames_dir=frames_dir, workspace_dir=workspace_dir, output_ply=output_ply)
        paths.sparse_dir.mkdir(parents=True, exist_ok=True)
        paths.text_model_dir.mkdir(parents=True, exist_ok=True)
        paths.output_ply.parent.mkdir(parents=True, exist_ok=True)

        commands = build_colmap_commands(
            executable=self.executable,
            paths=paths,
            matcher=clean_matcher,
            use_gpu=use_gpu,
        )
        for command in commands[:-2]:
            self._run(command)

        sparse_model_dir = find_sparse_model_dir(paths.sparse_dir)
        paths = ColmapPaths(
            database_path=paths.database_path,
            frames_dir=paths.frames_dir,
            sparse_dir=paths.sparse_dir,
            sparse_model_dir=sparse_model_dir,
            text_model_dir=paths.text_model_dir,
            output_ply=paths.output_ply,
        )

        text_command, ply_command = build_colmap_conversion_commands(self.executable, paths)
        self._run(text_command)
        self._run(ply_command)

        if not paths.output_ply.is_file():
            raise ColmapRunnerError("COLMAP finished without writing sparse-point-cloud.ply.")

        model_metadata = parse_colmap_text_model(paths.text_model_dir)
        registered_image_count = len(model_metadata.registered_images)
        sparse_point_count = count_sparse_points(paths.text_model_dir / "points3D.txt")
        ply_point_count = read_ascii_ply_vertex_count(paths.output_ply)

        return ColmapRunResult(
            executable=self.executable,
            matcher=clean_matcher,
            use_gpu=use_gpu,
            workspace_dir=workspace_dir,
            output_ply=paths.output_ply,
            registered_image_count=registered_image_count,
            sparse_point_count=sparse_point_count,
            ply_point_count=ply_point_count,
            command_count=len(commands),
            model_metadata=model_metadata,
        )

    def _run(self, command: Sequence[str]) -> None:
        completed = self._command_runner(command)
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            detail = stderr or stdout or f"exit code {completed.returncode}"
            raise ColmapRunnerError(f"COLMAP command failed: {Path(command[0]).name} {command[1]}: {detail}")

    @staticmethod
    def _run_subprocess(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
        )


def resolve_colmap_executable(configured_path: str | None = None) -> str:
    if configured_path:
        candidate = Path(configured_path).expanduser()
        if not candidate.is_file():
            raise ColmapRunnerError(f"Configured COLMAP executable was not found: {configured_path}")
        return str(candidate.resolve())

    discovered = shutil.which("colmap") or shutil.which("colmap.exe")
    if discovered:
        return discovered

    raise ColmapRunnerError(
        "COLMAP was not found. Install COLMAP for Windows and add colmap.exe to PATH, "
        "or set ROOMSPLAT_COLMAP_PATH to the full colmap.exe path."
    )


def build_colmap_paths(frames_dir: Path, workspace_dir: Path, output_ply: Path) -> ColmapPaths:
    return ColmapPaths(
        database_path=workspace_dir / "database.db",
        frames_dir=frames_dir,
        sparse_dir=workspace_dir / "sparse",
        sparse_model_dir=workspace_dir / "sparse" / "0",
        text_model_dir=workspace_dir / "model-text",
        output_ply=output_ply,
    )


def validate_matcher(matcher: str) -> str:
    if matcher not in {"exhaustive", "sequential"}:
        raise ColmapRunnerError("matcher must be 'exhaustive' or 'sequential'.")
    return matcher


def build_colmap_commands(
    executable: str,
    paths: ColmapPaths,
    *,
    matcher: str,
    use_gpu: bool,
) -> list[list[str]]:
    clean_matcher = validate_matcher(matcher)
    gpu_flag = "1" if use_gpu else "0"
    matcher_command = "exhaustive_matcher" if clean_matcher == "exhaustive" else "sequential_matcher"
    return [
        [
            executable,
            "feature_extractor",
            "--database_path",
            str(paths.database_path),
            "--image_path",
            str(paths.frames_dir),
            "--ImageReader.single_camera",
            "1",
            "--FeatureExtraction.use_gpu",
            gpu_flag,
        ],
        [
            executable,
            matcher_command,
            "--database_path",
            str(paths.database_path),
            "--FeatureMatching.use_gpu",
            gpu_flag,
        ],
        [
            executable,
            "mapper",
            "--database_path",
            str(paths.database_path),
            "--image_path",
            str(paths.frames_dir),
            "--output_path",
            str(paths.sparse_dir),
        ],
        [
            executable,
            "model_converter",
            "--input_path",
            str(paths.sparse_model_dir),
            "--output_path",
            str(paths.text_model_dir),
            "--output_type",
            "TXT",
        ],
        [
            executable,
            "model_converter",
            "--input_path",
            str(paths.sparse_model_dir),
            "--output_path",
            str(paths.output_ply),
            "--output_type",
            "PLY",
        ],
    ]


def build_colmap_conversion_commands(executable: str, paths: ColmapPaths) -> tuple[list[str], list[str]]:
    commands = build_colmap_commands(executable, paths, matcher="exhaustive", use_gpu=False)
    return commands[-2], commands[-1]


def find_sparse_model_dir(sparse_dir: Path) -> Path:
    candidates = sorted(path for path in sparse_dir.iterdir() if path.is_dir())
    if not candidates:
        raise ColmapRunnerError("COLMAP did not produce a sparse model. Try more frames, slower camera motion, or more textured input.")
    preferred = sparse_dir / "0"
    return preferred if preferred in candidates else candidates[0]


def count_registered_images(images_txt: Path) -> int:
    if not images_txt.is_file():
        return 0
    return len(parse_colmap_images(images_txt))


def count_sparse_points(points_txt: Path) -> int:
    if not points_txt.is_file():
        return 0
    return len(_data_lines(points_txt))


def read_ascii_ply_vertex_count(ply_path: Path) -> int:
    try:
        with ply_path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                clean_line = line.strip()
                if clean_line.startswith("element vertex "):
                    return int(clean_line.split()[-1])
                if clean_line == "end_header":
                    break
    except OSError as exc:
        raise ColmapRunnerError("Could not read sparse point cloud PLY.") from exc
    return 0


def parse_colmap_text_model(text_model_dir: Path) -> ColmapModelMetadata:
    cameras = tuple(parse_colmap_cameras(text_model_dir / "cameras.txt"))
    registered_images = tuple(parse_colmap_images(text_model_dir / "images.txt"))
    return ColmapModelMetadata(
        cameras=cameras,
        registered_images=registered_images,
        trajectory_bounds=_trajectory_bounds(registered_images),
    )


def parse_colmap_cameras(cameras_txt: Path) -> list[ColmapCamera]:
    if not cameras_txt.is_file():
        return []
    cameras: list[ColmapCamera] = []
    for line in _data_lines(cameras_txt):
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            cameras.append(
                ColmapCamera(
                    camera_id=int(parts[0]),
                    model=parts[1],
                    width=int(parts[2]),
                    height=int(parts[3]),
                    params=tuple(float(value) for value in parts[4:]),
                )
            )
        except ValueError as exc:
            raise ColmapRunnerError(f"Could not parse COLMAP camera line: {line}") from exc
    return cameras


def parse_colmap_images(images_txt: Path) -> list[ColmapRegisteredImage]:
    if not images_txt.is_file():
        return []
    lines = _data_lines(images_txt)
    images: list[ColmapRegisteredImage] = []
    for index in range(0, len(lines), 2):
        line = lines[index].strip()
        if not line:
            continue
        parts = line.split(maxsplit=9)
        if len(parts) < 10:
            continue
        try:
            qvec = (float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4]))
            tvec = (float(parts[5]), float(parts[6]), float(parts[7]))
            images.append(
                ColmapRegisteredImage(
                    image_id=int(parts[0]),
                    camera_id=int(parts[8]),
                    name=parts[9],
                    qvec=qvec,
                    tvec=tvec,
                    center=_camera_center(qvec, tvec),
                )
            )
        except ValueError as exc:
            raise ColmapRunnerError(f"Could not parse COLMAP image line: {line}") from exc
    return images


def _camera_center(
    qvec: tuple[float, float, float, float],
    tvec: tuple[float, float, float],
) -> tuple[float, float, float]:
    rotation = _qvec_to_rotation_matrix(qvec)
    tx, ty, tz = tvec
    return tuple(
        round(
            -(
                rotation[0][axis] * tx
                + rotation[1][axis] * ty
                + rotation[2][axis] * tz
            ),
            8,
        )
        for axis in range(3)
    )


def _qvec_to_rotation_matrix(qvec: tuple[float, float, float, float]) -> tuple[tuple[float, float, float], ...]:
    qw, qx, qy, qz = qvec
    return (
        (
            1 - 2 * qy * qy - 2 * qz * qz,
            2 * qx * qy - 2 * qz * qw,
            2 * qz * qx + 2 * qy * qw,
        ),
        (
            2 * qx * qy + 2 * qz * qw,
            1 - 2 * qx * qx - 2 * qz * qz,
            2 * qy * qz - 2 * qx * qw,
        ),
        (
            2 * qz * qx - 2 * qy * qw,
            2 * qy * qz + 2 * qx * qw,
            1 - 2 * qx * qx - 2 * qy * qy,
        ),
    )


def _trajectory_bounds(registered_images: Sequence[ColmapRegisteredImage]) -> ColmapTrajectoryBounds | None:
    if not registered_images:
        return None
    centers = [image.center for image in registered_images]
    return ColmapTrajectoryBounds(
        min=tuple(min(center[axis] for center in centers) for axis in range(3)),
        max=tuple(max(center[axis] for center in centers) for axis in range(3)),
    )


def _data_lines(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
