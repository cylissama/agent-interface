from pathlib import Path

from pydantic_settings import BaseSettings


# Find the project root (where .env file is located)
# This file is in backend/app/, so go up two levels to get to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application configuration settings."""

    app_name: str = "Agent Interface"
    database_url: str = "sqlite:///./agent.db"
    llm_api_key: str | None = None
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"  # Default to faster 1B model (can be overridden in .env)
    
    # Google Gemini settings
    gemini_api_key: str | None = None

    class Config:
        env_file = str(ENV_FILE) if ENV_FILE.exists() else ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
