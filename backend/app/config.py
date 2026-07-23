from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, loaded from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    riot_api_key: str = ""
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"
    redis_url: str | None = None

    # CORS origins allowed to call the API (the Vite dev server by default)
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
