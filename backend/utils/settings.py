from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]
SECRETS_DIR = BACKEND_DIR / "secrets"


class Settings(BaseSettings):
    app_name: str = "Lumina Finance Platform"
    debug: bool = Field(default=False, validation_alias="APP_DEBUG")
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/lumina_finance"
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=SECRETS_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
