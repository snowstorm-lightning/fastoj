from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "FastOJ"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://fastoj:fastoj_secret@localhost:5432/fastoj"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Judge Configuration
    JUDGE_CONTAINER_IMAGE: str = "fastoj-judge:latest"
    JUDGE_USE_DOCKER: bool = True  # Use Docker for code execution (requires Docker daemon)
    JUDGE_TIMEOUT: int = 30  # seconds
    JUDGE_MAX_RETRIES: int = 3
    DEFAULT_TIME_LIMIT: int = 1000  # ms
    DEFAULT_MEMORY_LIMIT: int = 256  # MB

    # Queue
    JUDGE_QUEUE_NAME: str = "judge_tasks"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()
