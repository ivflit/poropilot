import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    riot_api_key: str = ""

    # AI provider selection. Leave AI_PROVIDER blank to auto-detect from whichever
    # key is set (Anthropic preferred), or set it explicitly to "anthropic"/"gemini".
    ai_provider: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"

    redis_url: str | None = None

    # Postgres — the app starts without it (auth routes are simply not mounted).
    database_url: str | None = None

    # JWT auth tokens.
    jwt_secret: str = ""  # required when database_url is set; random fallback for dev
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS origins allowed to call the API (the Vite dev server by default). When the
    # frontend and backend are hosted separately (Netlify + Render) the browser call is
    # cross-origin, so this has to be set in the environment — as a comma-separated
    # list, e.g. CORS_ORIGINS=https://poropilot.netlify.app,https://poropilot.app
    cors_origins: list[str] = ["http://localhost:5173"]

    # Optional regex for origins that can't be listed up front — Netlify deploy previews
    # and branch deploys get a fresh subdomain each time, e.g.
    # CORS_ORIGIN_REGEX=https://.*--poropilot\.netlify\.app
    cors_origin_regex: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept a comma-separated string as well as pydantic's default JSON list."""
        if not isinstance(value, str):
            return value

        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            return json.loads(text)

        # Trailing slashes never match the browser's Origin header — strip them.
        return [origin.strip().rstrip("/") for origin in text.split(",") if origin.strip()]


settings = Settings()
