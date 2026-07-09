from functools import lru_cache
from typing import Optional
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    base_url: str = Field(alias="BASE_URL", description="Base URL for the API")
    api_key: str = Field(alias="API_KEY", description="API Key")
    model_name: Optional[str] = Field(default=None, alias="MODEL_NAME", description="Model Name")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Log Level")
    default_scene: str = Field(default="general", alias="DEFAULT_SCENE", description="Default Scene")
    mysql_host: str = Field(alias="MYSQL_HOST", description="MySQL Host")
    mysql_port: int = Field(alias="MYSQL_PORT", description="MySQL Port")
    mysql_database: str = Field(alias="MYSQL_DATABASE", description="MySQL Database")
    mysql_user: str = Field(alias="MYSQL_USERNAME", description="MySQL User")
    mysql_password: str = Field(alias="MYSQL_PASSWORD", description="MySQL Password")
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def mysql_url(self) -> str:
        username = quote_plus(self.mysql_user)
        password = quote_plus(self.mysql_password)
        return (
            f"mysql+pymysql://{username}:{password}"
            f"@{self.mysql_host}:{self.mysql_port}/{quote_plus(self.mysql_database)}"
            f"?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
