import logging
from datetime import datetime, timezone
from typing import Any

from src.clients.usgs_client import UsgsClient
from src.database.mongodb import MongoDatabase
from src.services.metrics_service import hour_window, recalculate_window

logger = logging.getLogger(__name__)


def transform_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    properties = feature.get("properties", {})
    coordinates = feature.get("geometry", {}).get("coordinates", [])
    if not feature.get("id") or len(coordinates) < 3 or properties.get("time") is None:
        return None
    return {
        "event_id": feature["id"],
        "magnitude": properties.get("mag"),
        "location": properties.get("place") or "Unknown",
        "latitude": coordinates[1],
        "longitude": coordinates[0],
        "depth": coordinates[2],
        "event_time": datetime.fromtimestamp(properties["time"] / 1000, tz=timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }


def ingest_once(client: UsgsClient, database: MongoDatabase) -> int:
    changed_windows: set[str] = set()
    processed = 0
    for feature in client.fetch_latest():
        event = transform_feature(feature)
        if event is None:
            logger.warning("Skipping malformed USGS feature")
            continue
        result = database.earthquakes.replace_one(
            {"event_id": event["event_id"]},
            event,
            upsert=True,
        )
        if result.upserted_id is not None or result.modified_count:
            changed_windows.add(hour_window(event["event_time"]))
        processed += 1
    for window in changed_windows:
        recalculate_window(database, window)
    logger.info("USGS ingestion completed", extra={"processed": processed, "windows": len(changed_windows)})
    return processed
