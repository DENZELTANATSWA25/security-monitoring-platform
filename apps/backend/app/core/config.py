from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    APP_NAME: str = "Security Monitoring Platform"
    APP_ENV: str = "development"

    DATABASE_URL: str
    REDIS_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    GEOIP_DATABASE_PATH: str | None = None
    TRUSTED_PROXY_IPS: str = ""

    # Machine-to-machine authentication for external telemetry ingestion.
    INGESTION_API_KEY_HEADER: str = "X-Ingestion-Key"

    # Per-source telemetry ingestion rate limiting.
    INGESTION_RATE_LIMIT: int = 100
    INGESTION_RATE_WINDOW_SECONDS: int = 60

    # Telemetry source health monitoring.
    TELEMETRY_SOURCE_ONLINE_THRESHOLD_SECONDS: int = 300

    # ML anomaly-detection model artifacrs.
    ANOMALY_MODEL_DIRECTORY: str = "models/anomaly_detection"

    # Pydantic Settings v2 configuration.
    model_config = SettingsConfigDict(
        env_file=".env",
    )



settings = Settings()
