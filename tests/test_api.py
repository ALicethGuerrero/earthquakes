import pytest
from fastapi.testclient import TestClient

from src.api.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"


def test_earthquakes_endpoint_default():
    with TestClient(app) as client:
        # Assuming the DB may be empty, just verify schema and pagination defaults
        response = client.get("/earthquakes")
        assert response.status_code == 200
        data = response.json()
        # Should be a list (could be empty)
        assert isinstance(data, list)
        # If there are items, they should contain required fields
        if data:
            item = data[0]
            for field in ["event_id", "magnitude", "location", "latitude", "longitude", "depth", "event_time"]:
                assert field in item


def test_metrics_endpoint():
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            metric = data[0]
            for field in ["window", "earthquake_count", "average_magnitude", "max_magnitude", "magnitude_distribution"]:
                assert field in metric


def test_reports_endpoint_limit():
    with TestClient(app) as client:
        response = client.get("/reports?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        if data:
            report = data[0]
            for field in ["report_date", "total_events", "average_magnitude", "max_magnitude", "top_locations"]:
                assert field in report
