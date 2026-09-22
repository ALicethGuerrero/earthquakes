import logging
import time

from src.clients.usgs_client import UsgsClient
from src.config.logging_config import configure_logging
from src.config.settings import get_settings
from src.database.mongodb import MongoDatabase
from src.services.ingestion_service import ingest_once


if __name__ == "__main__":
    configure_logging()
    logger = logging.getLogger(__name__)
    settings = get_settings()
    database = MongoDatabase(settings)
    database.ensure_indexes()
    try:
        with UsgsClient(settings.usgs_api_url) as client:
            while True:
                try:
                    ingest_once(client, database)
                except Exception:
                    logger.exception("USGS ingestion failed")
                time.sleep(settings.ingestion_interval_seconds)
    finally:
        database.close()
