from typing import Set
from starlette.websockets import WebSocket

_active_connections: Set[WebSocket] = set()

def add_connection(ws: WebSocket) -> None:
    """Registra una conexión WebSocket."""
    _active_connections.add(ws)


def remove_connection(ws: WebSocket) -> None:
    """Elimina una conexión WebSocket."""
    _active_connections.discard(ws)


def get_active_connections() -> int:
    """Devuelve el recuento actual de conexiones WebSocket activas."""
    return len(_active_connections)
