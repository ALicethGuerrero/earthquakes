from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator

from src.config.logging_config import configure_logging
from src.database.mongodb import MongoDatabase
from src.config.settings import get_settings
from src.api.routes import earthquakes, metrics, reports
from fastapi.middleware.cors import CORSMiddleware
from src.api.middleware import RequestIDMiddleware
from src.config.cache_config import init_cache
from src.api.websocket import router as websocket_router

"""Crear la aplicación FastAPI con configuración completa.

- Configura el logger estructurado.
- Inicializa la base de datos (con fallback de dummy).
- Registra routers, CORS, middleware de request ID, caché y WebSocket.
"""

def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Configuración del logging estructurado
        configure_logging()
        try:
            database = MongoDatabase(settings)
            database.ensure_indexes()
        except Exception:
            database = None
        app.state.database = database
        yield
        if database is not None:
            database.close()

    app = FastAPI(title="Earthquake Events API", version="1.0.0", lifespan=lifespan)
    # Registro de routers de la API
    app.include_router(earthquakes.router)
    app.include_router(metrics.router)
    app.include_router(reports.router)
    # Exponer métricas Prometheus
    Instrumentator().instrument(app).expose(app, endpoint="/prometheus")
    # Habilitar CORS (permitir todos los orígenes)
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    # Middleware que añade un ID único a cada petición
    app.add_middleware(RequestIDMiddleware)
    # Inicializar caché de la aplicación
    init_cache(app)
    # Incluir router WebSocket
    app.include_router(websocket_router)

    @app.get("/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        if app.state.database is None:
            raise HTTPException(status_code=503, detail="MongoDB no disponible")
        app.state.database.ping()
        return {"status": "ok", "database": "ok"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return ready()

    return app


app = create_app()
