import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from src.database.mongodb import MongoDatabase


_LOCATION_PATTERN = re.compile(r"\bof\s+(.+)$", re.IGNORECASE)


def extract_location(place: str) -> str:
    match = _LOCATION_PATTERN.search(place)
    return match.group(1).strip() if match else place.strip()


def generate_hourly_report(database: MongoDatabase, report_date: datetime | None = None) -> dict[str, Any]:
    end = report_date or datetime.now(timezone.utc)
    end = end.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=1)
    events = list(database.earthquakes.find({"event_time": {"$gte": start, "$lt": end}}))
    magnitudes = [event["magnitude"] for event in events if event.get("magnitude") is not None]
    locations = Counter(extract_location(event.get("location", "Unknown")) for event in events)
    report = {
        "report_date": end,
        "total_events": len(events),
        "average_magnitude": sum(magnitudes) / len(magnitudes) if magnitudes else None,
        "max_magnitude": max(magnitudes) if magnitudes else None,
        "top_locations": [location for location, _ in locations.most_common(3)],
        "created_at": datetime.now(timezone.utc),
    }
    database.reports.replace_one({"report_date": end}, report, upsert=True)
    return report
