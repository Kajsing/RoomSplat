import json
import base64

from fastapi.testclient import TestClient

from app.main import app


def test_create_real_ply_export_copies_source_and_writes_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "PLY export"}).json()
    project_dir = tmp_path / project["id"]
    source = project_dir / "reconstruction" / "pointcloud.ply"
    source.write_text(_tiny_ply(), encoding="utf-8")
    source_artifact = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"][0]

    response = client.post(
        f"/projects/{project['id']}/exports",
        json={"source_artifact_id": source_artifact["id"], "format": "ply"},
    )

    assert response.status_code == 201
    export = response.json()
    export_path = project_dir / export["export_relative_path"]
    metadata_path = project_dir / export["metadata_path"]
    assert export["status"] == "real"
    assert export["artifact_type"] == "point_cloud_ply"
    assert export_path.read_text(encoding="utf-8") == _tiny_ply()
    assert json.loads(metadata_path.read_text(encoding="utf-8")) == export

    artifacts = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"]
    assert export["export_relative_path"] in {artifact["relative_path"] for artifact in artifacts}
    download = client.get(export["download_url"])
    assert download.status_code == 200
    assert "comment tiny test file" in download.text


def test_create_placeholder_ply_export_from_debug_report_is_labeled(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Placeholder export"}).json()
    project_dir = tmp_path / project["id"]
    report = project_dir / "metadata" / "reconstruction_spike.json"
    report.write_text(json.dumps({"status": "stop_condition_missing_dependencies"}), encoding="utf-8")
    debug_artifact = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"][0]

    response = client.post(
        f"/projects/{project['id']}/exports",
        json={"source_artifact_id": debug_artifact["id"], "format": "ply", "allow_placeholder": True},
    )

    assert response.status_code == 201
    export = response.json()
    export_path = project_dir / export["export_relative_path"]
    assert export["status"] == "placeholder"
    assert export["warning"] == "Placeholder export generated from reconstruction spike debug report; not a real reconstruction."
    assert "not a real reconstruction" in export_path.read_text(encoding="utf-8")
    artifacts = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"]
    placeholder = next(artifact for artifact in artifacts if artifact["relative_path"] == export["export_relative_path"])
    assert placeholder["description"] == "Placeholder export for workflow/debug testing. This is not a real reconstruction."


def test_create_placeholder_glb_export_from_debug_report_is_valid_glb(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Placeholder GLB"}).json()
    project_dir = tmp_path / project["id"]
    (project_dir / "metadata" / "reconstruction_spike.json").write_text("{}", encoding="utf-8")
    debug_artifact = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"][0]

    response = client.post(
        f"/projects/{project['id']}/exports",
        json={"source_artifact_id": debug_artifact["id"], "format": "glb", "allow_placeholder": True},
    )

    assert response.status_code == 201
    export = response.json()
    data = (project_dir / export["export_relative_path"]).read_bytes()
    assert export["status"] == "placeholder"
    assert export["artifact_type"] == "mesh_glb"
    assert data[:4] == b"glTF"


def test_debug_report_export_requires_placeholder_flag(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Reject debug"}).json()
    project_dir = tmp_path / project["id"]
    (project_dir / "metadata" / "reconstruction_spike.json").write_text("{}", encoding="utf-8")
    debug_artifact = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"][0]

    response = client.post(
        f"/projects/{project['id']}/exports",
        json={"source_artifact_id": debug_artifact["id"], "format": "ply"},
    )

    assert response.status_code == 400
    assert "allow_placeholder" in response.text


def test_export_rejects_format_mismatch(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Mismatch"}).json()
    project_dir = tmp_path / project["id"]
    (project_dir / "reconstruction" / "pointcloud.ply").write_text(_tiny_ply(), encoding="utf-8")
    source_artifact = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"][0]

    response = client.post(
        f"/projects/{project['id']}/exports",
        json={"source_artifact_id": source_artifact["id"], "format": "glb"},
    )

    assert response.status_code == 400
    assert "does not match" in response.text


def test_list_exports_returns_metadata(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "List exports"}).json()
    project_dir = tmp_path / project["id"]
    (project_dir / "reconstruction" / "splat.ply").write_text(_tiny_ply(), encoding="utf-8")
    source_artifact = client.get(f"/projects/{project['id']}/artifacts").json()["artifacts"][0]
    created = client.post(
        f"/projects/{project['id']}/exports",
        json={"source_artifact_id": source_artifact["id"], "format": "ply"},
    ).json()

    response = client.get(f"/projects/{project['id']}/exports")

    assert response.status_code == 200
    assert response.json()["exports"] == [created]


def test_export_rejects_forged_artifact_path_escape(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)
    project = client.post("/projects", json={"name": "Path safety"}).json()
    forged_id = base64.urlsafe_b64encode(b"../outside.ply").decode("ascii").rstrip("=")

    response = client.post(
        f"/projects/{project['id']}/exports",
        json={"source_artifact_id": forged_id, "format": "ply"},
    )

    assert response.status_code == 400
    assert "invalid" in response.text


def _tiny_ply() -> str:
    return "\n".join(
        [
            "ply",
            "format ascii 1.0",
            "comment tiny test file",
            "element vertex 1",
            "property float x",
            "property float y",
            "property float z",
            "end_header",
            "0 0 0",
            "",
        ]
    )
