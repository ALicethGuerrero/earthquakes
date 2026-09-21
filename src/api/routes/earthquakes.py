from datetime import datetime
from typing import Any

from fastapi import APIRouter, Query, Request

from src.metadata.schemas import EarthquakeResponse, PaginationParams, serialize_document

router = APIRouter(prefix="/earthquakes", tags=["earthquakes"])


@router.get("", response_model=list[EarthquakeResponse])
def list_earthquakes(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    min_magnitude: float | None = Query(None, ge=-10, le=10),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    sort_by: str = Query("event_time", pattern="^(event_time|magnitude)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
) -> list[dict[str, Any]]:
    params = PaginationParams(
        skip=skip,
        limit=limit,
        min_magnitude=min_magnitude,
        start_date=start_date,
        end_date=end_date,
        sort_by=sort_by,
        order=order,
    )
    filters: dict[str, Any] = {}
    if params.min_magnitude is not None:
        filters["magnitude"] = {"$gte": params.min_magnitude}
    if params.start_date or params.end_date:
        filters["event_time"] = {}
        if params.start_date:
            filters["event_time"]["$gte"] = params.start_date
        if params.end_date:
            filters["event_time"]["$lte"] = params.end_date
    direction = -1 if params.order == "desc" else 1
    cursor = (
        request.app.state.database.earthquakes.find(filters)
        .sort(params.sort_by, direction)
        .skip(params.skip)
        .limit(params.limit)
    )
    return [serialize_document(document) for document in cursor]
