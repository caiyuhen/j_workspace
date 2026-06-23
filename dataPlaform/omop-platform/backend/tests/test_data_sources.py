import pytest

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200

def test_create_data_source(client):
    payload = {
        "name": "Hospital A API",
        "type": "api",
        "connection_string": "http://hospital-a/api/patients"
    }
    response = client.post("/api/v1/sources/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Hospital A API"
    assert "id" in data

def test_list_data_sources(client):
    response = client.get("/api/v1/sources/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_data_source(client):
    payload = {
        "name": "Hospital B",
        "type": "PostgreSQL",
        "connection_string": "postgresql://test"
    }
    create_resp = client.post("/api/v1/sources/", json=payload)
    source_id = create_resp.json()["id"]

    update_payload = {
        "name": "Hospital B Updated",
        "type": "PostgreSQL",
        "connection_string": "postgresql://test"
    }
    response = client.put(f"/api/v1/sources/{source_id}", json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Hospital B Updated"
