from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.models.earthquake import EarthquakeResponse
from src.models.metric import MetricResponse
from src.models.report import ReportResponse


class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1, le=200)
    min_magnitude: float | None = Field(default=None, ge=-10, le=10)
    start_date: datetime | None = None
    end_date: datetime | None = None
    sort_by: Literal["event_time", "magnitude"] = "event_time"
    order: Literal["asc", "desc"] = "desc"


class HealthResponse(BaseModel):
    status: str
    database: str


def serialize_document(document: dict[str, Any]) -> dict[str, Any]:
    document.pop("_id", None)
    return document


__all__ = [
    "EarthquakeResponse",
    "MetricResponse",
    "ReportResponse",
    "PaginationParams",
    "HealthResponse",
    "serialize_document",
]
