from datetime import datetime, timezone

from src.services.ingestion_service import transform_feature
from src.services.metrics_service import magnitude_bucket


def test_transform_feature_maps_usgs_geojson():
    feature = {
        "id": "us-test",
        "properties": {"mag": 4.2, "place": "20 km NW of California", "time": 1718610000000},
        "geometry": {"coordinates": [-120.12, 35.44, 10.5]},
    }

    event = transform_feature(feature)

    assert event["event_id"] == "us-test"
    assert event["longitude"] == -120.12
    assert event["latitude"] == 35.44
    assert event["event_time"].tzinfo == timezone.utc


def test_magnitude_bucket_defines_expected_ranges():
    assert magnitude_bucket(2.9) == "<3"
    assert magnitude_bucket(4.2) == "3-5"
    assert magnitude_bucket(5.0) == "5-7"
    assert magnitude_bucket(7.0) == ">=7"

def test_recalculate_window_month_boundary(monkeypatch):
    """Ensure recalculate_window works for a window that rolls over month boundary.
    Uses a fabricated in‑memory MongoDatabase with a dummy collection.
    """
    from datetime import datetime
    from src.services.metrics_service import recalculate_window
    from src.database.mongodb import MongoDatabase

    class DummyColl:
        def __init__(self):
            self.docs = []
        def insert_many(self, docs):
            self.docs.extend(docs)
        def aggregate(self, pipeline):
            # Simplified: return empty list, metrics will be generated as empty defaults
            return []
        def find_one(self, filter):
            return None
        def replace_one(self, filter, doc, upsert=False):
            pass

    class DummyDB(MongoDatabase):
        def __init__(self):
            # Bypass Settings
            pass
        @property
        def earthquakes(self):
            return DummyColl()
        @property
        def metrics(self):
            return DummyColl()
        def ensure_indexes(self):
            pass
        def close(self):
            pass

    db = DummyDB()
    # Window 2026-01-31T23 should not raise
    metric = recalculate_window(db, "2026-01-31T23")
    assert metric["window"] == "2026-01-31T23"
    assert metric["earthquake_count"] == 0
    assert metric["avg_magnitude"] is None
