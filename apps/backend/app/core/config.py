from pydantic import field_validator
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

    #Comma-separated browser origins permitted by CORS.
    CORS_ORIGINS: str = (
        "http://localhost:3000,"
        "http://127.0.0.1:3000"
    )

    #Interactive login abuse protection
    LOGIN_RATE_LIMIT_PER_EMAIL: int = 10
    LOGIN_RATE_LIMIT_PER_IP: int = 30
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 300

    GEOIP_DATABASE_PATH: str | None = None
    TRUSTED_PROXY_IPS: str = ""

    # Machine-to-machine authentication for external telemetry ingestion.
    INGESTION_API_KEY_HEADER: str = "X-Ingestion-Key"

    # Per-source telemetry ingestion rate limiting.
    INGESTION_RATE_LIMIT: int = 100
    INGESTION_RATE_WINDOW_SECONDS: int = 60

    # Telemetry source health monitoring.
    TELEMETRY_SOURCE_ONLINE_THRESHOLD_SECONDS: int = 300

    # ML anomaly-detection model artifacts.
    ANOMALY_MODEL_DIRECTORY: str = "models/anomaly_detection"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @field_validator("APP_ENV")
    @classmethod
    def validate_environment(cls, value: str) -> str:
        """Restrict the application to known runtime environments."""

        normalized = value.lower()

        allowed = {
            "development",
            "test",
            "production",
        }

        if normalized not in allowed:
            raise ValueError(
                "APP_ENV must be development, test, or production."
            )

        return normalized

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        """Reject unsafe JWT secrets in production."""

        if not value.strip():
            raise ValueError("JWT_SECRET_KEY must not be empty.")

        return value

    @property
    def cors_origins(self) -> list[str]:
        """Return configured CORS origins as normalised values."""

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]



settings = Settings()
