from __future__ import annotations

from pathlib import Path

from pipeline.adapters.base import (
    AdapterAssessment,
    ReconstructionArtifact,
    ReconstructionInput,
    dependencies_available,
    executable_dependency,
    python_module_dependency,
)


class NerfstudioSplatfactoAdapter:
    name = "nerfstudio-splatfacto"
    description = "Interim Gaussian Splatting training path through Nerfstudio Splatfacto."

    def assess(self, reconstruction_input: ReconstructionInput) -> AdapterAssessment:
        dependencies = [
            executable_dependency("ns-process-data"),
            executable_dependency("ns-train"),
            python_module_dependency("nerfstudio"),
            python_module_dependency("torch"),
        ]
        ready = dependencies_available(dependencies) and reconstruction_input.frame_count >= 3
        status = "ready" if ready else "missing_dependencies"
        if reconstruction_input.frame_count < 3:
            status = "insufficient_input"

        return AdapterAssessment(
            adapter=self.name,
            status=status,
            summary=(
                "Nerfstudio Splatfacto is the recommended interim full splat-training path once dependencies are installed."
            ),
            dependencies=dependencies,
            expected_outputs=[
                ReconstructionArtifact(
                    name="splat.ply",
                    path=Path("reconstruction/splat.ply"),
                    artifact_type="splat_ply",
                    description="Gaussian splat PLY output, not a conventional point cloud.",
                ),
            ],
            next_steps=[
                "Install Nerfstudio in an isolated conda environment on Windows.",
                "Use COLMAP/SfM initialization where possible before training Splatfacto.",
                "Keep this adapter replaceable by faster learned or generative splat methods.",
            ],
        )


def assess(reconstruction_input: ReconstructionInput) -> AdapterAssessment:
    return NerfstudioSplatfactoAdapter().assess(reconstruction_input)
