from datetime import datetime, timezone
from typing import Any

from src.database.mongodb import MongoDatabase


def magnitude_bucket(magnitude: float | None) -> str:
    if magnitude is None:
        return "unknown"
    if magnitude < 3:
        return "<3"
    if magnitude < 5:
        return "3-5"
    if magnitude < 7:
        return "5-7"
    return ">=7"


def hour_window(event_time: datetime) -> str:
    return event_time.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")


def recalculate_window(database: MongoDatabase, window: str) -> dict[str, Any]:
    start = datetime.fromisoformat(f"{window}:00:00+00:00")
    end = start.replace(hour=start.hour + 1) if start.hour < 23 else start.replace(day=start.day + 1, hour=0)
    pipeline = [
        {"$match": {"event_time": {"$gte": start, "$lt": end}}},
        {
            "$set": {
                "magnitude_bucket": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$magnitude", None]}, "then": "unknown"},
                            {"case": {"$lt": ["$magnitude", 3]}, "then": "<3"},
                            {"case": {"$lt": ["$magnitude", 5]}, "then": "3-5"},
                            {"case": {"$lt": ["$magnitude", 7]}, "then": "5-7"},
                        ],
                        "default": ">=7",
                    }
                }
            }
        },
        {
            "$group": {
                "_id": {"window": window, "bucket": "$magnitude_bucket"},
                "bucket_count": {"$sum": 1},
                "magnitude_sum": {"$sum": {"$ifNull": ["$magnitude", 0]}},
                "magnitude_count": {
                    "$sum": {"$cond": [{"$ne": ["$magnitude", None]}, 1, 0]}
                },
                "max_magnitude": {"$max": "$magnitude"},
            }
        },
        {
            "$group": {
                "_id": "$_id.window",
                "earthquake_count": {"$sum": "$bucket_count"},
                "magnitude_sum": {"$sum": "$magnitude_sum"},
                "magnitude_count": {"$sum": "$magnitude_count"},
                "max_magnitude": {"$max": "$max_magnitude"},
                "distribution": {"$push": {"k": "$_id.bucket", "v": "$bucket_count"}},
            }
        },
        {
            "$set": {
                "window": "$_id",
                "average_magnitude": {
                    "$cond": [
                        {"$gt": ["$magnitude_count", 0]},
                        {"$divide": ["$magnitude_sum", "$magnitude_count"]},
                        None,
                    ]
                },
                "magnitude_distribution": {"$arrayToObject": "$distribution"},
                "updated_at": "$$NOW",
            }
        },
        {"$unset": ["_id", "magnitude_sum", "magnitude_count", "distribution"]},
        {
            "$merge": {
                "into": "metrics",
                "on": "window",
                "whenMatched": "replace",
                "whenNotMatched": "insert",
            }
        },
    ]
    list(database.earthquakes.aggregate(pipeline))
    metric = database.metrics.find_one({"window": window})
    if metric is not None:
        metric.pop("_id", None)
        return metric
    metric = {
        "window": window,
        "earthquake_count": 0,
        "average_magnitude": None,
        "max_magnitude": None,
        "magnitude_distribution": {},
        "updated_at": datetime.now(timezone.utc),
    }
    database.metrics.replace_one({"window": window}, metric, upsert=True)
    return metric
