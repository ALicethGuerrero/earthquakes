import pytest
from fastapi.testclient import TestClient

import src.api.main as api_main


class EmptyCollection:
    def find(self, *args, **kwargs):
        return self

    def sort(self, *args, **kwargs):
        return self

    def skip(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(())


class FakeDatabase:
    earthquakes = EmptyCollection()
    metrics = EmptyCollection()
    reports = EmptyCollection()

    def __init__(self, settings):
        pass

    def ensure_indexes(self):
        pass

    def ping(self):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def fake_database(monkeypatch):
    monkeypatch.setattr(api_main, "MongoDatabase", FakeDatabase)


    api_main.app = api_main.create_app()


def test_health_endpoint():
    with TestClient(api_main.app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"


def test_earthquakes_endpoint_default():
    with TestClient(api_main.app) as client:
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
    with TestClient(api_main.app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            metric = data[0]
            for field in ["window", "earthquake_count", "avg_magnitude", "max_magnitude", "magnitude_distribution"]:
                assert field in metric


def test_reports_endpoint_limit():
    with TestClient(api_main.app) as client:
        response = client.get("/reports?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5
        if data:
            report = data[0]
            for field in ["report_date", "total_events", "average_magnitude", "max_magnitude", "top_locations"]:
                assert field in report
