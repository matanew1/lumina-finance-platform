from functools import lru_cache
from pathlib import Path
import logging
import sys

from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_DATABASE_URL = f"sqlite:///{(BACKEND_DIR / 'lumina.db').as_posix()}"
DEFAULT_CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
LOG_FORMAT = "%(levelname)s: %(message)s | [%(name)s] | %(funcName)s | %(asctime)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class Settings(BaseSettings):
    app_name: str = Field(default="Lumina Finance Platform", validation_alias="APP_NAME")
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    auto_init_db: bool = Field(default=True, validation_alias="AUTO_INIT_DB")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    database_url: str = Field(
        default=DEFAULT_SQLITE_DATABASE_URL,
        validation_alias="DATABASE_URL",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: DEFAULT_CORS_ORIGINS.copy(),
        validation_alias="CORS_ORIGINS",
    )

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (init_settings, env_settings, dotenv_settings, file_secret_settings)


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
