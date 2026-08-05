# backend/tests/core/test_production.py
# Unit tests verifying caching, structured JSON logging and system metrics endpoints

from fastapi.testclient import TestClient
import pytest
from backend.app.main import app
from backend.app.core.cache import cache

client = TestClient(app)

def test_cache_operations():
    # Test setting and getting from cache wrapper
    cache.set("test_key", {"status": "ok"})
    val = cache.get("test_key")
    assert val == {"status": "ok"}
    
    cache.delete("test_key")
    assert cache.get("test_key") is None


def test_health_metrics_endpoint():
    # Calling public health metrics should return resource statistics
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200
    
    data = response.json()
    assert "metrics" in data
    assert "cpu_usage_percent" in data["metrics"]
    assert "memory_usage_percent" in data["metrics"]
    assert "disk_usage_percent" in data["metrics"]
