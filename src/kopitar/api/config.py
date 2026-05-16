"""
API Configuration Settings

Centralized configuration management for the Kopitar API using Pydantic settings.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "Kopitar NHL Analytics API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(False)

    # API Configuration
    API_HOST: str = Field("0.0.0.0")
    API_PORT: int = Field(8000)
    API_PREFIX: str = "/api/v1"

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"]
    )

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://kopitar_user:kopitar_pass@localhost:5432/kopitar_nhl"
    )
    DATABASE_ECHO: bool = Field(False)

    # Redis Cache
    REDIS_URL: str = Field("redis://localhost:6379/0")
    CACHE_TTL: int = Field(300)  # 5 minutes

    # InfluxDB
    INFLUXDB_URL: str = Field("http://localhost:8086")
    INFLUXDB_TOKEN: str = Field("")
    INFLUXDB_ORG: str = Field("kopitar_org")
    INFLUXDB_BUCKET: str = Field("nhl_metrics")

    # NHL API — new endpoints (old statsapi.web.nhl.com deprecated Nov 2023)
    NHL_API_BASE_URL: str = Field(
        default="https://api-web.nhle.com/v1",
        validation_alias="NHL_API_BASE_URL",
    )
    NHL_WEB_API_BASE_URL: str = Field(
        default="https://api-web.nhle.com/v1",
        validation_alias="NHL_WEB_API_BASE_URL",
    )
    NHL_STATS_API_BASE_URL: str = Field(
        default="https://api.nhle.com/stats/rest/en",
        validation_alias="NHL_STATS_API_BASE_URL",
    )
    NHL_API_TIMEOUT: float = Field(30.0)
    NHL_API_RATE_LIMIT: int = Field(100)

    # Security
    SECRET_KEY: str = Field("")
    JWT_SECRET_KEY: str = Field("")
    JWT_ALGORITHM: str = Field("HS256")
    JWT_EXPIRATION_HOURS: int = Field(24)

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(1000)
    RATE_LIMIT_WINDOW: int = Field(3600)  # 1 hour

    # Logging
    LOG_LEVEL: str = Field("INFO")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File Paths
    DATA_PATH: str = Field("./data")
    MODELS_PATH: str = Field("./models")
    LOGS_PATH: str = Field("./logs")
    CACHE_PATH: str = Field("./cache")

    # Processing
    MAX_WORKERS: int = Field(4)
    BATCH_SIZE: int = Field(1000)
    PARALLEL_REQUESTS: int = Field(10)

    # Monitoring
    ENABLE_METRICS: bool = Field(True)
    METRICS_PORT: int = Field(9090)
    SENTRY_DSN: Optional[str] = Field(None)

    # Cloud Storage (Optional)
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None)
    AWS_DEFAULT_REGION: str = Field("us-east-1")
    AWS_BUCKET_NAME: Optional[str] = Field(None)

    GCP_PROJECT_ID: Optional[str] = Field(None)
    GCP_BUCKET_NAME: Optional[str] = Field(None)

    # Advanced Configuration
    ENABLE_PROFILING: bool = Field(False)
    MAX_MEMORY_USAGE_MB: int = Field(8192)

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: object) -> object:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def secret_key_required(cls, v: str) -> str:
        if not v and not os.getenv("DEBUG", "false").lower() == "true":
            raise ValueError("SECRET_KEY is required in production")
        return v or "dev-secret-key-change-in-production"

    @field_validator("JWT_SECRET_KEY", mode="after")
    @classmethod
    def jwt_secret_key_required(cls, v: str) -> str:
        if not v:
            return "dev-jwt-secret-change-in-production"
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "populate_by_name": True,
        "extra": "ignore",
    }


class DevelopmentSettings(Settings):
    """Development-specific settings."""

    DEBUG: bool = True
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENABLE_PROFILING: bool = True

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8888",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8888",
    ]


class ProductionSettings(Settings):
    """Production-specific settings."""

    DEBUG: bool = False
    DATABASE_ECHO: bool = False
    LOG_LEVEL: str = "INFO"
    ENABLE_PROFILING: bool = False

    RATE_LIMIT_REQUESTS: int = 500
    RATE_LIMIT_WINDOW: int = 3600


class TestSettings(Settings):
    """Test-specific settings."""

    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./test.db"
    REDIS_URL: str = "redis://localhost:6379/1"
    CACHE_TTL: int = 1

    ENABLE_METRICS: bool = False
    NHL_API_TIMEOUT: float = 5.0


@lru_cache()
def get_settings() -> Settings:
    """Get application settings based on environment, cached after first call."""
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# Export settings instance
settings = get_settings()
