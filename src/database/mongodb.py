from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.config.settings import Settings


class MongoDatabase:
    def __init__(self, settings: Settings) -> None:
        from pymongo import MongoClient

        self.client = MongoClient(
            settings.mongo_uri,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=10000,
        )
        self.database = self.client[settings.mongo_database]

    @property
    def earthquakes(self) -> Any:
        return self.database["earthquakes"]

    @property
    def metrics(self) -> Any:
        return self.database["metrics"]

    @property
    def reports(self) -> Any:
        return self.database["hourly_reports"]

    def ensure_indexes(self) -> None:
        from pymongo import DESCENDING

        self.earthquakes.create_index("event_id", unique=True)
        self.earthquakes.create_index([("event_time", DESCENDING)])
        self.earthquakes.create_index([("magnitude", DESCENDING)])
        self.metrics.create_index("window", unique=True)
        self.reports.create_index("report_date", unique=True)

    def ping(self) -> None:
        self.client.admin.command("ping")

    def close(self) -> None:
        self.client.close()


def get_database() -> Generator[MongoDatabase, None, None]:
    from src.config.settings import get_settings

    database = MongoDatabase(get_settings())
    try:
        yield database
    finally:
        database.close()
