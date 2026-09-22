import logging
import json
from datetime import datetime, timezone
from typing import Any

import redis

from src.clients.usgs_client import UsgsClient
from src.config.settings import Settings, get_settings
from src.database.mongodb import MongoDatabase
from src.services.metrics_service import hour_window, recalculate_window

logger = logging.getLogger(__name__)


def publish_event(settings: Settings, event: dict[str, Any]) -> None:
    """Publica un evento para los clientes WebSocket."""
    try:
        client = redis.Redis.from_url(settings.redis_uri, decode_responses=True)
        client.publish("earthquakes", json.dumps(event))
        client.close()
    except Exception:
        logger.warning("WebSocket event publication failed", exc_info=True)


def transform_feature(feature: dict[str, Any]) -> dict[str, Any] | None:
    """
    Transforma una característica (feature) del GeoJSON de USGS al modelo interno de la aplicación.
    Retorna None si la estructura del evento es malformada o incompleta.
    """
    properties = feature.get("properties", {})
    coordinates = feature.get("geometry", {}).get("coordinates", [])
    
    # Validar que el evento tenga ID, coordenadas válidas (longitud, latitud, profundidad) y marca de tiempo
    magnitude = properties.get("mag")
    timestamp = properties.get("time")
    if (
        not feature.get("id")
        or len(coordinates) < 3
        or timestamp is None
        or any(not isinstance(value, (int, float)) for value in coordinates[:3])
        or not isinstance(timestamp, (int, float))
        or (magnitude is not None and not isinstance(magnitude, (int, float)))
    ):
        return None
        
    return {
        "event_id": feature["id"],
        "magnitude": magnitude,
        "location": properties.get("place") or "Unknown",
        "latitude": coordinates[1],
        "longitude": coordinates[0],
        "depth": coordinates[2],
        "event_time": datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc),
    }


def ingest_once(
    client: UsgsClient,
    database: MongoDatabase,
    settings: Settings | None = None,
) -> int:
    """
    Ejecuta un ciclo de ingesta desde la API de USGS hacia MongoDB.
    
    Proceso:
    1. Obtiene los eventos más recientes de la API de USGS.
    2. Transforma cada evento e inserta/actualiza (upsert) en la colección de earthquakes.
    3. Si hay eventos nuevos o modificados, registra métricas y los transmite a la cola de WebSockets.
    4. Recalcula las ventanas horarias afectadas para mantener las métricas al día.
    """
    settings = settings or get_settings()
    changed_windows: set[str] = set()
    processed = 0
    
    for feature in client.fetch_latest():
        event = transform_feature(feature)
        if event is None:
            logger.warning("Skipping malformed USGS feature")
            continue
            
        existing = database.earthquakes.find_one({"event_id": event["event_id"]})
        if existing is not None:
            fields = ("magnitude", "location", "latitude", "longitude", "depth", "event_time")
            if all(existing.get(field) == event[field] for field in fields):
                processed += 1
                continue
            changed_windows.add(hour_window(existing["event_time"]))

        event["updated_at"] = datetime.now(timezone.utc)
        result = database.earthquakes.replace_one(
            {"event_id": event["event_id"]},
            event,
            upsert=True,
        )
        
        # Si el evento fue insertado por primera vez o actualizado
        if result.upserted_id is not None or result.modified_count:
            changed_windows.add(hour_window(event["event_time"]))
            
            # Registrar métricas personalizadas para el evento procesado
            from src.metrics.custom_metrics import record_event_processed, record_event_duration
            record_event_processed(source="usgs")
            
            # Duración aproximada (se establece en 0.0 por simplicidad)
            record_event_duration(source="usgs", duration=0.0)
            
            publish_event(settings, {
                "event_id": event["event_id"],
                "magnitude": event["magnitude"],
                "time": event["event_time"].isoformat(),
            })
            
        processed += 1
        
    # Recalcular únicamente las ventanas de tiempo que recibieron cambios
    for window in changed_windows:
        recalculate_window(database, window)
    logger.info("USGS ingestion completed", extra={"processed": processed, "windows": len(changed_windows)})
    return processed