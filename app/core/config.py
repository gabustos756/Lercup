import os
from urllib.parse import urlparse
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ENV: str = "development"
    SECRET_KEY: str = "devsecretkeychangeitpostmvp"
    DATABASE_URL: str = "sqlite:///database.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    @model_validator(mode="after")
    def enforce_production_database(self) -> "Settings":
        if self.ENV != "production":
            return self

        if self.DATABASE_URL.startswith("sqlite"):
            env_set = bool(os.environ.get("DATABASE_URL", "").strip())
            hint = (
                "DATABASE_URL is not in os.environ (using SQLite default)."
                if not env_set
                else "DATABASE_URL resolves to SQLite."
            )
            raise ValueError(
                f"SQLite is not allowed in production. {hint} "
                "On Railway, open the web service -> Variables -> "
                "Add Reference -> Postgres -> DATABASE_URL."
            )

        if not self.DATABASE_URL.startswith("postgresql"):
            raise ValueError(
                f"Unsupported DATABASE_URL scheme in production: "
                f"{self.DATABASE_URL.split('://', 1)[0]}://. "
                "Expected postgresql://."
            )

        return self

def database_url_for_log(url: str) -> str:
    """Return DATABASE_URL with credentials redacted for safe logging."""
    parsed = urlparse(url)
    host = parsed.hostname or "unknown"
    port = f":{parsed.port}" if parsed.port else ""
    database = (parsed.path or "").lstrip("/") or "unknown"
    return f"{parsed.scheme}://***@{host}{port}/{database}"

settings = Settings()
