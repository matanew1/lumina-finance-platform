from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
SECRETS_DIR = BACKEND_DIR / "utils" / "secrets"


class Settings(BaseSettings):
    app_name: str = "Lumina Finance Platform"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    auto_init_db: bool = Field(default=True, validation_alias="AUTO_INIT_DB")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lumina_finance"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=SECRETS_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache # Cache the settings instance to avoid re-reading the .env file multiple times
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
