"""
Automated test suite for Progressive Web App (PWA) capabilities.
Verifies manifest metadata, service worker routing, icons, and shell templates.
"""
from fastapi.testclient import TestClient


def test_pwa_manifest_endpoint(client: TestClient):
    """Test that /manifest.json returns valid PWA configuration."""
    response = client.get("/manifest.json")
    assert response.status_code == 200
    assert "application/manifest+json" in response.headers.get("content-type", "")
    
    data = response.json()
    assert data["name"] == "ResearchDose — Scientific Preclinical Dose Converter"
    assert data["short_name"] == "ResearchDose"
    assert data["display"] == "standalone"
    assert data["start_url"] == "/"
    assert len(data["icons"]) >= 3
    assert len(data["shortcuts"]) >= 3


def test_pwa_service_worker_endpoint(client: TestClient):
    """Test that /sw.js is served with root scope permission."""
    response = client.get("/sw.js")
    assert response.status_code == 200
    assert "application/javascript" in response.headers.get("content-type", "")
    assert response.headers.get("service-worker-allowed") == "/"
    assert "researchdose-" in response.text
    assert "PRECACHE_ASSETS" in response.text


def test_pwa_favicon_endpoint(client: TestClient):
    """Test that /favicon.ico is reachable."""
    response = client.get("/favicon.ico")
    assert response.status_code == 200
    assert "image/x-icon" in response.headers.get("content-type", "")


def test_pwa_icons_static_files(client: TestClient):
    """Test that PWA icons are served correctly via /static/icons/."""
    for icon_path in [
        "/static/icons/icon-192x192.png",
        "/static/icons/icon-512x512.png",
        "/static/icons/icon-maskable-512x512.png",
        "/static/icons/icon.svg",
        "/static/icons/apple-touch-icon.png",
    ]:
        resp = client.get(icon_path)
        assert resp.status_code == 200, f"Failed to fetch {icon_path}"
        assert len(resp.content) > 100


def test_homepage_includes_pwa_elements(client: TestClient):
    """Test that the homepage HTML links the manifest and contains PWA UI components."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.text

    # Manifest link and Apple meta tags
    assert 'rel="manifest" href="/manifest.json"' in html
    assert 'name="mobile-web-app-capable" content="yes"' in html
    assert 'apple-touch-icon' in html

    # PWA install button and network badge
    assert 'id="btnInstallPwa"' in html
    assert 'id="networkStatusBadge"' in html
    assert 'id="iosInstallModal"' in html
    assert 'id="pwaOfflineToast"' in html
