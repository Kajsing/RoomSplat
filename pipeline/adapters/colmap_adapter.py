from __future__ import annotations

from pathlib import Path

from pipeline.adapters.base import (
    AdapterAssessment,
    ReconstructionArtifact,
    ReconstructionInput,
    executable_dependency,
    python_module_dependency,
)


class ColmapPoseAdapter:
    name = "colmap"
    description = "Camera pose estimation and sparse reconstruction using COLMAP or pycolmap."

    def assess(self, reconstruction_input: ReconstructionInput) -> AdapterAssessment:
        dependencies = [
            executable_dependency("colmap"),
            python_module_dependency("pycolmap"),
        ]
        has_any_colmap = any(dependency.available for dependency in dependencies)
        status = "ready" if has_any_colmap and reconstruction_input.frame_count >= 3 else "missing_dependencies"
        if reconstruction_input.frame_count < 3:
            status = "insufficient_input"

        return AdapterAssessment(
            adapter=self.name,
            status=status,
            summary=(
                "COLMAP is the preferred pose-estimation layer for the interim splat pipeline."
                if has_any_colmap
                else "COLMAP or pycolmap is needed to estimate camera poses from extracted frames."
            ),
            dependencies=dependencies,
            expected_outputs=[
                ReconstructionArtifact(
                    name="cameras.json",
                    path=Path("reconstruction/cameras.json"),
                    artifact_type="camera_poses",
                    description="Camera intrinsics/extrinsics for downstream splat training.",
                ),
                ReconstructionArtifact(
                    name="pointcloud.ply",
                    path=Path("reconstruction/pointcloud.ply"),
                    artifact_type="point_cloud_ply",
                    description="Sparse conventional point cloud from SfM, not Gaussian splats.",
                ),
            ],
            next_steps=[
                "Install COLMAP binaries or pycolmap.",
                "Run SfM on project frames before splat optimization.",
            ],
        )


def assess(reconstruction_input: ReconstructionInput) -> AdapterAssessment:
    return ColmapPoseAdapter().assess(reconstruction_input)
