import json

from fastapi.testclient import TestClient

from app.main import app


def test_geometry_bundle_endpoint_returns_valid_complete_bundle(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Geometry bundle"}).json()
    project_dir = tmp_path / project["id"]
    _write_bundle_files(project_dir)
    (project_dir / "metadata" / "geometry_bundle.json").write_text(json.dumps(_valid_bundle(project["id"])), encoding="utf-8")

    response = client.get(f"/projects/{project['id']}/geometry-bundle")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "roomsplat.geometry_bundle.v1"
    assert payload["artifact_type"] == "learned_geometry_bundle"
    assert payload["mode"] == "learned_geometry"
    assert payload["source_adapter"] == "lingbot-map-contract-smoke"
    assert payload["complete"] is True
    assert payload["is_reconstruction"] is False
    assert payload["not_reconstruction"] is True
    assert payload["capabilities"] == {"depth": True, "confidence": True, "mask": False, "pointmap": True}


def test_geometry_bundle_artifact_listing_labels_predicted_outputs(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Geometry artifacts"}).json()
    project_dir = tmp_path / project["id"]
    _write_bundle_files(project_dir)
    (project_dir / "metadata" / "geometry_bundle.json").write_text(json.dumps(_valid_bundle(project["id"])), encoding="utf-8")
    (project_dir / "reconstruction" / "sparse-point-cloud.ply").write_text(_tiny_ply(), encoding="utf-8")

    response = client.get(f"/projects/{project['id']}/artifacts")

    assert response.status_code == 200
    artifacts = response.json()["artifacts"]
    labels = {artifact["relative_path"]: artifact["artifact_type"] for artifact in artifacts}
    assert labels["reconstruction/learned-point-cloud.ply"] == "predicted_point_cloud_ply"
    assert labels["metadata/geometry_bundle.json"] == "learned_geometry_bundle"
    assert labels["reconstruction/sparse-point-cloud.ply"] == "point_cloud_ply"
    predicted = next(artifact for artifact in artifacts if artifact["artifact_type"] == "predicted_point_cloud_ply")
    assert predicted["viewer_supported"] is True
    assert "predicted" in predicted["description"].lower()
    bundle = next(artifact for artifact in artifacts if artifact["artifact_type"] == "learned_geometry_bundle")
    assert bundle["viewer_supported"] is False


def test_geometry_bundle_rejects_incomplete_bundle(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Incomplete bundle"}).json()
    project_dir = tmp_path / project["id"]
    _write_bundle_files(project_dir)
    bundle = _valid_bundle(project["id"])
    bundle["status"] = "incomplete"
    bundle["complete"] = False
    (project_dir / "metadata" / "geometry_bundle.json").write_text(json.dumps(bundle), encoding="utf-8")

    response = client.get(f"/projects/{project['id']}/geometry-bundle")
    artifacts = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"]

    assert response.status_code == 400
    assert "incomplete" in response.text
    assert "metadata/geometry_bundle.json" not in {artifact["relative_path"] for artifact in artifacts}


def test_geometry_bundle_rejects_escaped_sidecar_path(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Escaped bundle"}).json()
    project_dir = tmp_path / project["id"]
    _write_bundle_files(project_dir)
    bundle = _valid_bundle(project["id"])
    bundle["sidecars"][0]["relative_path"] = "../outside/depth.npz"
    (project_dir / "metadata" / "geometry_bundle.json").write_text(json.dumps(bundle), encoding="utf-8")

    response = client.get(f"/projects/{project['id']}/geometry-bundle")
    artifacts = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"]

    assert response.status_code == 400
    assert "escaped" in response.text
    assert "reconstruction/learned-point-cloud.ply" not in {artifact["relative_path"] for artifact in artifacts}


def test_geometry_bundle_rejects_missing_primary_artifact(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Missing primary"}).json()
    project_dir = tmp_path / project["id"]
    _write_bundle_files(project_dir, write_primary=False)
    (project_dir / "metadata" / "geometry_bundle.json").write_text(json.dumps(_valid_bundle(project["id"])), encoding="utf-8")

    response = client.get(f"/projects/{project['id']}/geometry-bundle")

    assert response.status_code == 400
    assert "was not found" in response.text


def test_geometry_bundle_rejects_reconstruction_flag_conflict(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Flag conflict"}).json()
    project_dir = tmp_path / project["id"]
    _write_bundle_files(project_dir)
    bundle = _valid_bundle(project["id"])
    bundle["is_reconstruction"] = True
    (project_dir / "metadata" / "geometry_bundle.json").write_text(json.dumps(bundle), encoding="utf-8")

    response = client.get(f"/projects/{project['id']}/geometry-bundle")

    assert response.status_code == 400
    assert "is_reconstruction false" in response.text


def _write_bundle_files(project_dir, *, write_primary: bool = True) -> None:
    (project_dir / "frames").mkdir(parents=True, exist_ok=True)
    (project_dir / "metadata" / "learned").mkdir(parents=True, exist_ok=True)
    (project_dir / "reconstruction").mkdir(parents=True, exist_ok=True)
    (project_dir / "frames" / "frame_000001.png").write_bytes(b"png")
    (project_dir / "frames" / "frame_000002.png").write_bytes(b"png")
    (project_dir / "metadata" / "learned" / "depth_000001.npz").write_bytes(b"depth")
    (project_dir / "metadata" / "learned" / "confidence_000001.npz").write_bytes(b"confidence")
    if write_primary:
        (project_dir / "reconstruction" / "learned-point-cloud.ply").write_text(_tiny_ply(), encoding="utf-8")


def _valid_bundle(project_id: str) -> dict:
    return {
        "project_id": project_id,
        "schema_version": "roomsplat.geometry_bundle.v1",
        "artifact_type": "learned_geometry_bundle",
        "mode": "learned_geometry",
        "source_adapter": "lingbot-map-contract-smoke",
        "adapter_family": "feed_forward",
        "status": "complete",
        "complete": True,
        "is_reconstruction": False,
        "not_reconstruction": True,
        "frame_count": 2,
        "frame_index_map": [
            {"bundle_frame_index": 0, "source_frame_index": 0, "source_frame": "frames/frame_000001.png"},
            {"bundle_frame_index": 1, "source_frame_index": 1, "source_frame": "frames/frame_000002.png"},
        ],
        "cameras": [
            {"frame_index": 0, "position": {"x": 0.0, "y": 0.0, "z": 0.0}, "qvec": [1.0, 0.0, 0.0, 0.0]},
            {"frame_index": 1, "position": {"x": 1.0, "y": 0.0, "z": 0.0}, "qvec": [1.0, 0.0, 0.0, 0.0]},
        ],
        "intrinsics": [
            {"frame_index": 0, "width": 8, "height": 6, "fx": 6.0, "fy": 6.0, "cx": 4.0, "cy": 3.0},
            {"frame_index": 1, "width": 8, "height": 6, "fx": 6.0, "fy": 6.0, "cx": 4.0, "cy": 3.0},
        ],
        "trajectory": [
            {"frame_index": 0, "position": {"x": 0.0, "y": 0.0, "z": 0.0}},
            {"frame_index": 1, "position": {"x": 1.0, "y": 0.0, "z": 0.0}},
        ],
        "capabilities": {"depth": True, "confidence": True, "mask": False, "pointmap": True},
        "primary_artifacts": [
            {
                "relative_path": "reconstruction/learned-point-cloud.ply",
                "artifact_type": "predicted_point_cloud_ply",
                "role": "primary",
                "description": "Predicted point cloud from a learned geometry adapter smoke manifest.",
            }
        ],
        "sidecars": [
            {
                "relative_path": "metadata/learned/depth_000001.npz",
                "sidecar_type": "depth",
                "required": True,
                "description": "Depth sidecar declaration.",
            },
            {
                "relative_path": "metadata/learned/confidence_000001.npz",
                "sidecar_type": "confidence",
                "required": True,
                "description": "Confidence sidecar declaration.",
            },
        ],
        "quality": {"status": "needs_review", "notes": "Contract smoke only; not a real model run."},
        "warnings": ["Predicted geometry is not a verified metric scan."],
        "generated_data_rules": {
            "local_only": True,
            "no_auto_downloads": True,
            "contained_under_project": True,
            "ignored_by_git": True,
            "notes": "Generated learned geometry files stay under ignored project data.",
        },
    }


def _tiny_ply() -> str:
    return "\n".join(
        [
            "ply",
            "format ascii 1.0",
            "element vertex 1",
            "property float x",
            "property float y",
            "property float z",
            "end_header",
            "0 0 0",
            "",
        ]
    )
