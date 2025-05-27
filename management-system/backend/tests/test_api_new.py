import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    # Note: DB check might fail in test environment, that's expected


def test_app_startup():
    """Test that the FastAPI app starts correctly."""
    assert app is not None
    assert hasattr(app, "routes")


def test_cors_middleware():
    """Test that CORS middleware is configured."""
    # Check if CORS middleware is added to the app
    middleware_found = False
    for middleware in app.user_middleware:
        if hasattr(middleware, "cls"):
            cls_name = getattr(middleware.cls, "__name__", "")
            if cls_name == "CORSMiddleware":
                middleware_found = True
                break

    assert middleware_found, "CORS middleware not found in app middleware stack"


def test_api_routes_registered():
    """Test that API routes are registered."""
    # Get route paths from FastAPI app
    route_paths = []
    for route in app.routes:
        # Use getattr to safely access path attribute
        if hasattr(route, "path"):
            route_paths.append(getattr(route, "path", ""))

    # Check that health endpoint exists
    assert (
        "/api/health" in route_paths
    ), f"Health endpoint not found in routes: {route_paths}"

    # Check for API routes (should have more than just health endpoint)
    api_routes = [path for path in route_paths if path.startswith("/api")]
    assert len(api_routes) > 1, f"Expected more API routes, found: {api_routes}"


@pytest.mark.asyncio
async def test_health_endpoint_structure():
    """Test the structure of health endpoint response."""
    response = client.get("/api/health")
    data = response.json()

    # Should have status field
    assert "status" in data

    # Should have db field (might be 'ok' or 'unavailable' depending on DB connection)
    assert "db" in data
    assert data["db"] in ["ok", "unavailable"]
