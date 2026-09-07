"""Application configuration from environment variables."""
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Settings can be overridden via:
    1. Environment variables
    2. .env file in the project root
    3. Class defaults
    """

    # Application
    APP_NAME: str = "LogPulse"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://logpulse:logpulse@localhost:5432/logpulse_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Bootstrap admin account (created/promoted on startup if ADMIN_PASSWORD is set)
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@logpulse.local"
    ADMIN_PASSWORD: str = ""  # Must be set via environment variable to enable bootstrap

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # LLM Configuration
    OPENAI_API_KEY: str = ""  # Must be set via environment variable
    LLM_MODEL: str = "gpt-4"
    LLM_TEMPERATURE: float = 0.7

    class Config:
        """Pydantic settings configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()

__all__ = ["Settings", "settings"]
