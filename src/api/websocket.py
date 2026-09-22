import json

import redis.asyncio as redis
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.config.settings import get_settings
from src.config.websocket_state import add_connection, remove_connection

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/earthquakes")
async def earthquakes_ws(websocket: WebSocket, min_magnitude: float | None = None):
    """Transmite eventos sísmicos publicados en Redis."""
    await websocket.accept()
    add_connection(websocket)
    client = redis.from_url(get_settings().redis_uri, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe("earthquakes")
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                continue
            event = json.loads(message["data"])
            if min_magnitude is not None and event.get("magnitude") is not None:
                if float(event["magnitude"]) < min_magnitude:
                    continue
            await websocket.send_json(event)
    except WebSocketDisconnect:
        remove_connection(websocket)
    except Exception as exc:
        remove_connection(websocket)
        raise exc
    finally:
        await pubsub.unsubscribe("earthquakes")
        await pubsub.close()
        await client.close()
