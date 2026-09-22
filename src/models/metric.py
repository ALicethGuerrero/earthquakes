from pydantic import BaseModel, Field


class MetricResponse(BaseModel):
    window: str
    earthquake_count: int
    avg_magnitude: float | None
    max_magnitude: float | None
    magnitude_distribution: dict[str, int] = Field(default_factory=dict)
