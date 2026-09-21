from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from src.config.logging_config import configure_logging
from src.database.mongodb import MongoDatabase
from src.config.settings import get_settings
from src.api.routes import earthquakes, metrics, reports


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_logging()
        database = MongoDatabase(settings)
        database.ensure_indexes()
        app.state.database = database
        yield
        database.close()

    app = FastAPI(title="Earthquake Events API", version="1.0.0", lifespan=lifespan)
    app.include_router(earthquakes.router)
    app.include_router(metrics.router)
    app.include_router(reports.router)
    Instrumentator().instrument(app).expose(app, endpoint="/prometheus")

    @app.get("/live")
    def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        app.state.database.ping()
        return {"status": "ok", "database": "ok"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return ready()

    return app


app = create_app()
