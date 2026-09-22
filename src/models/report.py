from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    report_date: datetime
    total_events: int
    average_magnitude: float | None
    max_magnitude: float | None
    top_locations: list[str]
