"""
Health check tests for HealthLang AI MVP.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data


def test_health_detailed(client: TestClient):
    """Test detailed health check endpoint."""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "uptime" in data
    assert "version" in data


def test_health_readiness(client: TestClient):
    """Test readiness check endpoint."""
    response = client.get("/health/readiness")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]


def test_health_liveness(client: TestClient):
    """Test liveness check endpoint."""
    response = client.get("/health/liveness")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert data["status"] in ["alive", "dead"]


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint."""
    response = client.get("/metrics")
    assert response.status_code == 200
    
    # Should return Prometheus metrics format
    content = response.text
    assert "healthlang_" in content or "# HELP" in content


@pytest.mark.asyncio
async def test_health_check_async(async_client):
    """Test health check with async client."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_health_check_with_query_params(client: TestClient):
    """Test health check with query parameters."""
    response = client.get("/health?detailed=true&include_metrics=true")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "services" in data


def test_health_check_invalid_endpoint(client: TestClient):
    """Test invalid health endpoint returns 404."""
    response = client.get("/health/invalid")
    assert response.status_code == 404


def test_health_check_response_format(client: TestClient):
    """Test health check response format."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    
    # Check required fields
    required_fields = ["status", "timestamp", "version"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Check data types
    assert isinstance(data["status"], str)
    assert isinstance(data["timestamp"], str)
    assert isinstance(data["version"], str)
    
    # Check status values
    valid_statuses = ["healthy", "unhealthy", "degraded"]
    assert data["status"] in valid_statuses


def test_health_check_headers(client: TestClient):
    """Test health check response headers."""
    response = client.get("/health")
    assert response.status_code == 200
    
    headers = response.headers
    assert "content-type" in headers
    assert "application/json" in headers["content-type"]


def test_health_check_cors_headers(client: TestClient):
    """Test CORS headers in health check response."""
    response = client.options("/health")
    assert response.status_code in [200, 405]  # OPTIONS might not be implemented
    
    if response.status_code == 200:
        headers = response.headers
        # Check for CORS headers if implemented
        if "access-control-allow-origin" in headers:
            assert headers["access-control-allow-origin"] in ["*", "https://healthcare-mcp.onrender.com"]


def test_health_check_performance(client: TestClient):
    """Test health check response time."""
    import time
    
    start_time = time.time()
    response = client.get("/health")
    end_time = time.time()
    
    assert response.status_code == 200
    
    # Health check should be fast (less than 1 second)
    response_time = end_time - start_time
    assert response_time < 1.0, f"Health check took too long: {response_time:.2f}s"


def test_health_check_concurrent_requests(client: TestClient):
    """Test health check with concurrent requests."""
    import threading
    import time
    
    results = []
    errors = []
    
    def make_request():
        try:
            response = client.get("/health")
            results.append(response.status_code)
        except Exception as e:
            errors.append(str(e))
    
    # Start multiple threads
    threads = []
    for _ in range(5):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 5
    assert all(status == 200 for status in results), f"Not all requests succeeded: {results}" 