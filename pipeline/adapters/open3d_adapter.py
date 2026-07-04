from __future__ import annotations

from pathlib import Path

from pipeline.adapters.base import (
    AdapterAssessment,
    ReconstructionArtifact,
    ReconstructionInput,
    python_module_dependency,
)


class Open3DDebugAdapter:
    name = "open3d-debug"
    description = "Optional point-cloud inspection and conversion tooling, not a splat trainer."

    def assess(self, reconstruction_input: ReconstructionInput) -> AdapterAssessment:
        dependency = python_module_dependency("open3d")
        return AdapterAssessment(
            adapter=self.name,
            status="ready" if dependency.available else "optional_missing",
            summary="Open3D is useful for inspecting conventional point clouds but does not replace splat training.",
            dependencies=[dependency],
            expected_outputs=[
                ReconstructionArtifact(
                    name="pointcloud.ply",
                    path=Path("reconstruction/pointcloud.ply"),
                    artifact_type="point_cloud_ply",
                    description="Conventional point cloud for debug inspection.",
                ),
            ],
            next_steps=[
                "Install open3d if local point-cloud inspection is needed.",
                "Keep splat PLY and point-cloud PLY labels separate in the UI.",
            ],
        )


def assess(reconstruction_input: ReconstructionInput) -> AdapterAssessment:
    return Open3DDebugAdapter().assess(reconstruction_input)
