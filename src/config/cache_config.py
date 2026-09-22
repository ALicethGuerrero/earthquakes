import os
from fastapi import FastAPI
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

"""Configuración del caché de la aplicación.

Define el TTL (tiempo de vida) por defecto y una función para inicializar
FastAPI‑Cache con un backend en memoria.
# NOTE: el backend en memoria es rápido para pruebas, pero no persiste entre reinicios.
"""

CACHE_TTL = int(os.getenv("CACHE_TTL", "5"))

def init_cache(app: FastAPI) -> None:
    """Inicializa FastAPI‑Cache con un backend en memoria.

    Se debe llamar una única vez al iniciar la aplicación, después de crear la instancia ``FastAPI``.
    """
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
