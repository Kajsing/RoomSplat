from __future__ import annotations

from pathlib import Path

from pipeline.adapters.base import (
    AdapterAssessment,
    ReconstructionArtifact,
    ReconstructionInput,
    dependencies_available,
    python_module_dependency,
)


class GsplatResearchAdapter:
    name = "gsplat"
    description = "Lower-level Gaussian Splatting research backend and future fast/generative upgrade target."

    def assess(self, reconstruction_input: ReconstructionInput) -> AdapterAssessment:
        dependencies = [
            python_module_dependency("torch"),
            python_module_dependency("gsplat"),
        ]
        ready = dependencies_available(dependencies) and reconstruction_input.frame_count >= 3
        status = "ready" if ready else "missing_dependencies"
        if reconstruction_input.frame_count < 3:
            status = "insufficient_input"

        return AdapterAssessment(
            adapter=self.name,
            status=status,
            summary="gsplat is a good adapter boundary for faster custom or learned Gaussian Splatting later.",
            dependencies=dependencies,
            expected_outputs=[
                ReconstructionArtifact(
                    name="splat.ply",
                    path=Path("reconstruction/splat.ply"),
                    artifact_type="splat_ply",
                    description="Gaussian splat artifact produced by a custom gsplat training/export path.",
                ),
            ],
            next_steps=[
                "Install PyTorch with a matching CUDA build.",
                "Install gsplat using a wheel or Windows build path matching the PyTorch/CUDA versions.",
                "Use this adapter for later learned/generative splat experiments after the standard pipeline works.",
            ],
        )


def assess(reconstruction_input: ReconstructionInput) -> AdapterAssessment:
    return GsplatResearchAdapter().assess(reconstruction_input)
