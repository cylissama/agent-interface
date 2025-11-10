from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    app_name: str = "Agent Interface"
    database_url: str = "sqlite:///./agent.db"
    llm_api_key: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
