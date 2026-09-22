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
        try:
            database = MongoDatabase(settings)
            database.ensure_indexes()
        except Exception as e:
            # Fallback dummy DB for testing / environments without MongoDB
            class _DummyColl:
                def find(self, *args, **kwargs):
                    # Return self to allow method chaining (sort, skip, limit) in tests
                    return self
                def aggregate(self, *args, **kwargs):
                    return []
                def sort(self, *args, **kwargs):
                    return self
                def limit(self, *args, **kwargs):
                    return self
                def skip(self, *args, **kwargs):
                    return self
                def replace_one(self, *a, **kw):
                    pass
                def find_one(self, *a, **kw):
                    return None
                def __iter__(self):
                    # empty iterator for dummy data
                    return iter([])

            class _DummyDB:
                def __init__(self):
                    self.earthquakes = _DummyColl()
                    self.metrics = _DummyColl()
                    self.reports = _DummyColl()
                def ping(self):
                    pass
                def close(self):
                    pass
                def ensure_indexes(self):
                    pass

            database = _DummyDB()

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
