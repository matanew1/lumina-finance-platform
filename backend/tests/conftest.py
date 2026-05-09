import os

os.environ.setdefault("APP_NAME", "Lumina Finance Platform Test")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("AUTO_INIT_DB", "false")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:5173"]')

from backend.tests.helpers.api import api_client

__all__ = ["api_client"]
