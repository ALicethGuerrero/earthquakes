from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = Field(default="mongodb://localhost:27017", validation_alias="MONGO_URI")
    mongo_database: str = Field(default="earthquakes", validation_alias="MONGO_DATABASE")
    usgs_api_url: str = Field(
        default="https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson",
        validation_alias="USGS_API_URL",
    )
    ingestion_interval_seconds: int = Field(default=180, validation_alias="INGESTION_INTERVAL_SECONDS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
