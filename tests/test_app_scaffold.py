"""
Integration tests for FastAPI application endpoints.
"""

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Test /health returns online status and proper counts."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["verified_species_count"] >= 12
    assert data["total_species_count"] >= 13
    assert data["scientific_references_count"] >= 5
    assert "preclinical" in data["scientific_disclaimer"].lower()


def test_species_api_endpoint(client: TestClient):
    """Test /api/species returns all species with provenance."""
    response = client.get("/api/species")
    assert response.status_code == 200
    data = response.json()
    assert "species" in data
    assert data["total_count"] >= 13
    assert data["verified_count"] >= 12

    # Check that mouse is present and verified
    mouse_entry = next((s for s in data["species"] if s["id"] == "mouse"), None)
    assert mouse_entry is not None
    assert float(mouse_entry["km_factor"]) == 3.0
    assert mouse_entry["verification_status"] == "verified"


def test_references_api_endpoint(client: TestClient):
    """Test /api/references returns verified scientific guidelines."""
    response = client.get("/api/references")
    assert response.status_code == 200
    data = response.json()
    assert "references" in data
    assert len(data["references"]) >= 5


def test_homepage_html_endpoint(client: TestClient):
    """Test GET / renders HTML dashboard with status 200."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "ResearchDose" in response.text
    assert "FDA Table 1" in response.text

