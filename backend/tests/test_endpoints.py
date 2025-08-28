import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Test the root endpoint
@pytest.mark.parametrize("endpoint", [
    "/auth/otp",
    "/auth/verify",
    "/me",
    "/me/consents",
    "/me/profile",
    "/evidence",
    "/score/compute",
    "/score/me",
    "/loan/quote",
    "/loan/apply",
    "/admin/applications",
])
def test_endpoints(endpoint):
    response = client.get(endpoint)
    assert response.status_code in [200, 401, 404]
