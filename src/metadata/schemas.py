from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EarthquakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    magnitude: float | None
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: datetime


class MetricResponse(BaseModel):
    window: str
    earthquake_count: int
    average_magnitude: float | None
    max_magnitude: float | None
    magnitude_distribution: dict[str, int] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    report_date: datetime
    total_events: int
    average_magnitude: float | None
    max_magnitude: float | None
    top_locations: list[str]


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
