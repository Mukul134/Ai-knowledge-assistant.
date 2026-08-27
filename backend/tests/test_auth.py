import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_auth_me_endpoint_missing_token():
    """Test that requesting user metadata without a token fails with 401 Unauthorized (from HTTPBearer dependency)."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_auth_me_endpoint_invalid_token():
    """Test that requesting with a malformed token fails with 401 Unauthorized."""
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token-signature-12345"})
    assert response.status_code == 401
    assert "Authorization failure" in response.json()["detail"]

def test_auth_me_endpoint_mock_token():
    """
    Test that requesting with a valid mock token (starting with mock-)
    resolves the authenticated user mock properties successfully in development environment.
    """
    response = client.get("/api/auth/me", headers={"Authorization": "Bearer mock-test-token"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "de305d54-75b4-431b-adb2-eb6b9e546013"
    assert data["email"] == "developer@example.com"
    assert data["role"] == "authenticated"
