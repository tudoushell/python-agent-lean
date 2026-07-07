from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_url: str = Field(alias="BASE_URL", description="Base URL for the API")
    api_key: str = Field(alias="API_KEY", description="API Key")
    model_name: Optional[str] = Field(default=None, alias="MODEL_NAME", description="Model Name")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Log Level")
    default_scene: str = Field(default="general", alias="DEFAULT_SCENE", description="Default Scene")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )



@lru_cache
def get_settings() -> Settings:
    return Settings()