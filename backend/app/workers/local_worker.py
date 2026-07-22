from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.models.schemas import JobResponse
from app.services.debug_frame_cloud import DebugFrameCloudService
from app.services.frame_extraction import FrameExtractionService
from app.services.job_store import JobStore
from app.services.learned_geometry_import import LearnedGeometryImportService
from app.services.project_store import ProjectStore
from app.services.reconstruction_jobs import ReconstructionService
from app.services.splat_reconstruction import SplatReconstructionService

from pipeline.scripts.run_reconstruction_spike import build_report, inspect_frames, write_report


class LocalWorker:
    def __init__(self, project_store: ProjectStore, job_store: JobStore, config: AppConfig) -> None:
        self.project_store = project_store
        self.job_store = job_store
        self.config = config

    def run_job(self, project_id: str, job_id: str) -> JobResponse:
        job = self.job_store.mark_running(project_id, job_id)
        try:
            self.job_store.append_log(project_id, job_id, f"executing {job.job_type}")
            result = self._execute(job)
            return self.job_store.mark_succeeded(project_id, job_id, result)
        except Exception as exc:
            return self.job_store.mark_failed(project_id, job_id, str(exc))

    def _execute(self, job: JobResponse) -> dict[str, Any]:
        if job.job_type == "frame_extraction":
            return self._run_frame_extraction(job)
        if job.job_type == "reconstruction_spike":
            return self._run_reconstruction_spike(job)
        if job.job_type == "debug_frame_cloud":
            return self._run_debug_frame_cloud(job)
        if job.job_type == "reconstruct_point_cloud":
            return self._run_reconstruct_point_cloud(job)
        if job.job_type == "reconstruct_splat":
            return self._run_reconstruct_splat(job)
        if job.job_type == "learned_geometry_preflight":
            return self._run_learned_geometry_preflight(job)
        if job.job_type == "import_learned_geometry":
            return self._run_import_learned_geometry(job)
        raise ValueError(f"Unsupported job type: {job.job_type}")

    def _run_frame_extraction(self, job: JobResponse) -> dict[str, Any]:
        service = FrameExtractionService(
            self.project_store,
            ffmpeg_path=self.config.ffmpeg_path,
            ffmpeg_timeout_seconds=self.config.ffmpeg_timeout_seconds,
        )
        result = service.extract_frames(
            project_id=job.project_id,
            source_video=job.params.get("source_video"),
            stride=int(job.params.get("stride", 1)),
            max_frames=job.params.get("max_frames"),
        )
        self.job_store.append_log(job.project_id, job.id, f"extracted {result.extracted_frame_count} frames")
        return result.model_dump()

    def _run_reconstruction_spike(self, job: JobResponse) -> dict[str, Any]:
        project_dir = self.project_store.get_project_dir(job.project_id)
        frames_dir = _resolve_inside_project(project_dir, job.params.get("frames_dir") or "frames")
        reconstruction_input = inspect_frames(frames_dir)
        report = build_report(reconstruction_input, project_dir)
        report_path = write_report(project_dir, report)
        self.job_store.append_log(job.project_id, job.id, f"wrote reconstruction spike report: {report_path}")
        return report

    def _run_debug_frame_cloud(self, job: JobResponse) -> dict[str, Any]:
        service = DebugFrameCloudService(self.project_store)
        result = service.generate(
            job.project_id,
            max_points=job.params.get("max_points", 50_000),
            frame_step=job.params.get("frame_step", 1),
            arc_degrees=job.params.get("arc_degrees", 55.0),
            plane_width=job.params.get("plane_width", 1.35),
        )
        self.job_store.append_log(job.project_id, job.id, f"wrote debug frame cloud: {result['output_path']}")
        return result

    def _run_reconstruct_point_cloud(self, job: JobResponse) -> dict[str, Any]:
        service = ReconstructionService(self.project_store, colmap_path=self.config.colmap_path)
        result = service.reconstruct_point_cloud(
            job.project_id,
            matcher=job.params.get("matcher", "exhaustive"),
            use_gpu=job.params.get("use_gpu", False),
            preset=job.params.get("preset", "balanced"),
        )
        self.job_store.append_log(job.project_id, job.id, f"wrote sparse point cloud: {result['output_path']}")
        return result

    def _run_reconstruct_splat(self, job: JobResponse) -> dict[str, Any]:
        service = SplatReconstructionService(
            self.project_store,
            ns_process_data_path=self.config.ns_process_data_path,
            ns_train_path=self.config.ns_train_path,
            ns_export_path=self.config.ns_export_path,
            nerfstudio_bin_dir=self.config.nerfstudio_bin_dir,
            nerfstudio_python_path=self.config.nerfstudio_python_path,
            ffmpeg_path=self.config.ffmpeg_path,
            colmap_path=self.config.colmap_path,
        )
        result = service.reconstruct_splat(
            job.project_id,
            method=job.params.get("method", "splatfacto"),
            max_iterations=job.params.get("max_iterations"),
        )
        if result.get("output_path"):
            self.job_store.append_log(job.project_id, job.id, f"wrote Gaussian splat: {result['output_path']}")
        else:
            self.job_store.append_log(job.project_id, job.id, f"splat reconstruction not ready: {result['status']}")
        return result

    def _run_learned_geometry_preflight(self, job: JobResponse) -> dict[str, Any]:
        service = LearnedGeometryImportService(self.project_store)
        result = service.preflight(
            job.project_id,
            source_dir=job.params.get("source_dir"),
            source_adapter=job.params.get("source_adapter", "local-learned-geometry"),
            primary_ply=job.params.get("primary_ply", "points.ply"),
        )
        self.job_store.append_log(job.project_id, job.id, f"learned geometry import preflight ready: {result['frame_count']} mapped frames")
        return result

    def _run_import_learned_geometry(self, job: JobResponse) -> dict[str, Any]:
        service = LearnedGeometryImportService(self.project_store)
        result = service.import_output(
            job.project_id,
            source_dir=job.params.get("source_dir"),
            source_adapter=job.params.get("source_adapter", "local-learned-geometry"),
            primary_ply=job.params.get("primary_ply", "points.ply"),
        )
        self.job_store.append_log(job.project_id, job.id, "imported learned geometry bundle: metadata/geometry_bundle.json")
        return result


class WorkerPool:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="roomsplat-worker")
        self._futures: dict[str, Future[JobResponse]] = {}

    def submit(self, worker: LocalWorker, project_id: str, job_id: str) -> Future[JobResponse]:
        future = self._executor.submit(worker.run_job, project_id, job_id)
        self._futures[job_id] = future
        return future


worker_pool = WorkerPool()


def _resolve_inside_project(project_dir: Path, requested_path: Any) -> Path:
    candidate = Path(str(requested_path))
    if not candidate.is_absolute():
        candidate = project_dir / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(project_dir.resolve())
    except ValueError as exc:
        raise ValueError("Job path escaped the project directory.") from exc
    return resolved
