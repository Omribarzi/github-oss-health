"""
Tests for admin API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.config import settings


# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_admin_key(monkeypatch):
    """Mock admin API key for testing."""
    monkeypatch.setattr(settings, "admin_api_key", "test_admin_key")
    return "test_admin_key"


def test_admin_status_no_auth(client, test_db):
    """Test admin status endpoint without authentication."""
    response = client.get("/admin/status")
    assert response.status_code == 401
    assert "Missing X-Admin-Token" in response.json()["detail"]


def test_admin_status_invalid_auth(client, test_db, mock_admin_key):
    """Test admin status endpoint with invalid token."""
    response = client.get(
        "/admin/status",
        headers={"X-Admin-Token": "wrong_key"}
    )
    assert response.status_code == 403
    assert "Invalid admin token" in response.json()["detail"]


def test_admin_status_valid_auth(client, test_db, mock_admin_key):
    """Test admin status endpoint with valid authentication."""
    response = client.get(
        "/admin/status",
        headers={"X-Admin-Token": mock_admin_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "configuration" in data
    assert data["configuration"]["min_stars"] == 2000


def test_trigger_discovery_requires_auth(client, test_db):
    """Test discovery endpoint requires authentication."""
    response = client.post("/admin/trigger-discovery")
    assert response.status_code == 401


def test_trigger_deep_analysis_requires_auth(client, test_db):
    """Test deep analysis endpoint requires authentication."""
    response = client.post("/admin/trigger-deep-analysis")
    assert response.status_code == 401


def test_trigger_watchlist_requires_auth(client, test_db):
    """Test watchlist endpoint requires authentication."""
    response = client.post("/admin/trigger-watchlist")
    assert response.status_code == 401


def test_refresh_queue_requires_auth(client, test_db):
    """Test queue refresh endpoint requires authentication."""
    response = client.post("/admin/refresh-queue")
    assert response.status_code == 401


def test_admin_status_no_key_configured(client, test_db, monkeypatch):
    """Test admin status when API key is not configured."""
    monkeypatch.setattr(settings, "admin_api_key", None)
    response = client.get(
        "/admin/status",
        headers={"X-Admin-Token": "any_key"}
    )
    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]
