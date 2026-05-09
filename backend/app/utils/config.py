from functools import lru_cache
from pathlib import Path
import logging
import sys

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
LOG_FORMAT = "%(levelname)s: %(message)s | [%(name)s] | %(funcName)s | %(asctime)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class Settings(BaseSettings):
    app_name: str = Field(validation_alias="APP_NAME")
    debug: bool = Field(validation_alias="APP_DEBUG")
    auto_init_db: bool = Field(validation_alias="AUTO_INIT_DB")
    log_level: str = Field(validation_alias="LOG_LEVEL")
    database_url: str = Field(validation_alias="DATABASE_URL")
    cors_origins: list[str] = Field(validation_alias="CORS_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def configure_logging(log_level: str) -> None:
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        stream=sys.stdout,
        force=True,
    )
    logging.getLogger().setLevel(level)


settings = get_settings()
