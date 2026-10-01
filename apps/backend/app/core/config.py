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

    # Pydantic Settings v2 configuration.
    model_config = SettingsConfigDict(
        env_file=".env",
    )


settings = Settings()
