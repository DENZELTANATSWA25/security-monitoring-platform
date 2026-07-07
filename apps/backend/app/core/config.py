from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Security Monitoring Platform"
    APP_ENV: str = "development"

    DATABASE_URL: str

    REDIS_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"
        

settings = Settings()