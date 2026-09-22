from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EarthquakeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    magnitude: float | None
    location: str
    latitude: float
    longitude: float
    depth: float
    event_time: datetime
