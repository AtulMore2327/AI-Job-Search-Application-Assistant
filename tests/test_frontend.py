"""
Tests for Phase 11 Frontend integration, static assets, and UI endpoints.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

def test_frontend_files_exist():
    """Verify essential frontend files exist in the filesystem."""
    assert (FRONTEND_DIR / "index.html").exists()
    assert (FRONTEND_DIR / "css" / "style.css").exists()
    assert (FRONTEND_DIR / "js" / "api.js").exists()
    assert (FRONTEND_DIR / "js" / "ui.js").exists()
    assert (FRONTEND_DIR / "js" / "app.js").exists()

def test_get_root_returns_frontend():
    """Verify GET / returns the frontend HTML page."""
    response = client.get("/")
    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text or "<html" in response.text
    assert "AI Job Assistant" in response.text


def test_static_css_loads():
    """Verify static CSS asset is served properly."""
    response = client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "font-family" in response.text or "var(" in response.text

def test_static_js_loads():
    """Verify static JS assets are served properly."""
    r_api = client.get("/static/js/api.js")
    assert r_api.status_code == 200
    assert "class API" in r_api.text or "uploadResume" in r_api.text

    r_ui = client.get("/static/js/ui.js")
    assert r_ui.status_code == 200
    assert "class UI" in r_ui.text or "showToast" in r_ui.text

    r_app = client.get("/static/js/app.js")
    assert r_app.status_code == 200
    assert "AppState" in r_app.text or "initNavigation" in r_app.text

def test_api_routes_still_work():
    """Verify core backend API routes remain unaffected by static mounting."""
    h_res = client.get("/health")
    assert h_res.status_code == 200
    assert h_res.json()["status"] == "healthy"

    stats_res = client.get("/tracker/applications/stats")
    assert stats_res.status_code == 200
    assert "total_applications" in stats_res.json()
