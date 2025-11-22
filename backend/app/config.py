from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# Find the project root (where .env file is located)
# This file is in backend/app/, so go up two levels to get to project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields from .env file
        case_sensitive=False,  # Allow case-insensitive env var matching
    )

    app_name: str = "Agent Interface"
    database_url: str = "sqlite:///./agent.db"
    llm_api_key: str | None = None
    
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:1b"  # Default to faster 1B model (can be overridden in .env)
    
    # GROQ Minstrel API settings
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com"  # Default GROQ API base URL (uses /openai/v1/ endpoints)
    groq_model: str = "llama-3.1-8b-instant"  # GROQ model to use for Minstrel (current model, can be overridden in .env)


def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
