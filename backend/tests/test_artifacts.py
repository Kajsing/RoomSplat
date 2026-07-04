import json

from fastapi.testclient import TestClient
import pytest

from app.main import app


def test_artifact_listing_labels_reconstruction_and_debug_files(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Artifacts"}).json()
    project_dir = tmp_path / project["id"]

    (project_dir / "reconstruction" / "pointcloud.ply").write_text(_tiny_ply(), encoding="utf-8")
    (project_dir / "reconstruction" / "splat.ply").write_text(_tiny_ply(), encoding="utf-8")
    (project_dir / "exports" / "result.glb").write_bytes(b"glTF")
    (project_dir / "metadata" / "reconstruction_spike.json").write_text(
        json.dumps({"status": "stop_condition_missing_dependencies"}),
        encoding="utf-8",
    )

    response = client.get(f"/projects/{project['id']}/artifacts")

    assert response.status_code == 200
    artifacts = response.json()["artifacts"]
    labels = {artifact["relative_path"]: artifact["artifact_type"] for artifact in artifacts}
    assert labels == {
        "reconstruction/pointcloud.ply": "point_cloud_ply",
        "reconstruction/splat.ply": "splat_ply",
        "exports/result.glb": "mesh_glb",
        "metadata/reconstruction_spike.json": "debug_report",
    }
    assert {artifact["viewer_supported"] for artifact in artifacts if artifact["artifact_type"] == "debug_report"} == {True}
    assert {artifact["viewer_supported"] for artifact in artifacts if artifact["artifact_type"] == "mesh_glb"} == {True}


def test_artifact_download_serves_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Download"}).json()
    project_dir = tmp_path / project["id"]
    (project_dir / "reconstruction" / "pointcloud.ply").write_text(_tiny_ply(), encoding="utf-8")

    artifacts = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"]
    pointcloud = next(artifact for artifact in artifacts if artifact["artifact_type"] == "point_cloud_ply")
    response = client.get(pointcloud["download_url"])

    assert response.status_code == 200
    assert "ply" in response.text


def test_artifact_download_rejects_unknown_id(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Reject"}).json()

    response = client.get(f"/projects/{project['id']}/artifacts/not-real/download")

    assert response.status_code == 404


def test_artifact_listing_skips_symlink_escape(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path / "data"))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Symlink"}).json()
    project_dir = tmp_path / "data" / project["id"]
    outside = tmp_path / "outside.ply"
    outside.write_text(_tiny_ply(), encoding="utf-8")
    link = project_dir / "reconstruction" / "linked.ply"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation is not available in this Windows environment.")

    artifacts = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"]

    assert "reconstruction/linked.ply" not in {artifact["relative_path"] for artifact in artifacts}


def _tiny_ply() -> str:
    return "\n".join(
        [
            "ply",
            "format ascii 1.0",
            "element vertex 2",
            "property float x",
            "property float y",
            "property float z",
            "property uchar red",
            "property uchar green",
            "property uchar blue",
            "end_header",
            "0 0 0 255 0 0",
            "1 0 0 0 255 0",
            "",
        ]
    )
