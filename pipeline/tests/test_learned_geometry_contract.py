from pathlib import Path

import pytest

from pipeline.adapters import (
    GEOMETRY_BUNDLE_RELATIVE_PATH,
    LEARNED_GEOMETRY_BUNDLE_ARTIFACT_TYPE,
    PREDICTED_POINT_CLOUD_ARTIFACT_TYPE,
    ReconstructionArtifact,
    learned_geometry_expected_outputs,
    validate_geometry_expected_outputs,
)


def test_learned_geometry_expected_outputs_declare_bundle_and_predicted_cloud() -> None:
    artifacts = learned_geometry_expected_outputs()

    validate_geometry_expected_outputs(artifacts)

    labels = {artifact.artifact_type: artifact.path for artifact in artifacts}
    assert labels[LEARNED_GEOMETRY_BUNDLE_ARTIFACT_TYPE] == GEOMETRY_BUNDLE_RELATIVE_PATH
    assert labels[PREDICTED_POINT_CLOUD_ARTIFACT_TYPE] == Path("reconstruction") / "learned-point-cloud.ply"


def test_learned_geometry_contract_rejects_missing_bundle_manifest() -> None:
    artifacts = [
        ReconstructionArtifact(
            name="Predicted point cloud",
            path=Path("reconstruction") / "learned-point-cloud.ply",
            artifact_type=PREDICTED_POINT_CLOUD_ARTIFACT_TYPE,
            description="Predicted geometry.",
        )
    ]

    with pytest.raises(ValueError, match="metadata/geometry_bundle.json"):
        validate_geometry_expected_outputs(artifacts)


def test_learned_geometry_contract_rejects_escaped_paths() -> None:
    artifacts = learned_geometry_expected_outputs()
    artifacts.append(
        ReconstructionArtifact(
            name="Escaped sidecar",
            path=Path("..") / "outside.bin",
            artifact_type="depth_sidecar",
            description="Invalid path.",
        )
    )

    with pytest.raises(ValueError, match="project-relative"):
        validate_geometry_expected_outputs(artifacts)


def test_learned_geometry_contract_rejects_non_ply_predicted_cloud() -> None:
    artifacts = [
        ReconstructionArtifact(
            name="Geometry bundle manifest",
            path=GEOMETRY_BUNDLE_RELATIVE_PATH,
            artifact_type=LEARNED_GEOMETRY_BUNDLE_ARTIFACT_TYPE,
            description="Manifest.",
        ),
        ReconstructionArtifact(
            name="Predicted point cloud",
            path=Path("reconstruction") / "learned-point-cloud.obj",
            artifact_type=PREDICTED_POINT_CLOUD_ARTIFACT_TYPE,
            description="Predicted geometry.",
        ),
    ]

    with pytest.raises(ValueError, match=".ply"):
        validate_geometry_expected_outputs(artifacts)
