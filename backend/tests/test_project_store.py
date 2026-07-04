import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.project_store import PROJECT_SUBDIRECTORIES, ProjectStore, ProjectStoreError


def test_create_project_writes_metadata_and_directories(tmp_path) -> None:
    store = ProjectStore(tmp_path)

    project = store.create_project("  Living   room scan  ")
    project_path = tmp_path / project.id

    assert project.name == "Living room scan"
    assert project_path.exists()
    assert project.path == str(project_path.resolve())

    for subdirectory in PROJECT_SUBDIRECTORIES:
        assert (project_path / subdirectory).is_dir()

    metadata_path = project_path / "metadata" / "project.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["id"] == project.id
    assert metadata["name"] == "Living room scan"
    assert metadata["path"] == str(project_path.resolve())


def test_list_projects_reads_existing_metadata(tmp_path) -> None:
    store = ProjectStore(tmp_path)

    first_project = store.create_project("First")
    second_project = store.create_project("Second")

    projects = store.list_projects()

    assert [project.id for project in projects] == [second_project.id, first_project.id]


def test_create_project_rejects_blank_name(tmp_path) -> None:
    store = ProjectStore(tmp_path)

    with pytest.raises(ProjectStoreError):
        store.create_project("  ")


def test_projects_api_creates_and_lists_projects(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    create_response = client.post("/projects", json={"name": "Kitchen scan"})
    assert create_response.status_code == 201
    created_project = create_response.json()
    assert created_project["name"] == "Kitchen scan"

    list_response = client.get("/projects")
    assert list_response.status_code == 200
    assert list_response.json()["projects"] == [created_project]


def test_projects_api_rejects_blank_name(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ROOMSPLAT_DATA_DIR", str(tmp_path))
    client = TestClient(app)

    response = client.post("/projects", json={"name": " "})

    assert response.status_code == 400
