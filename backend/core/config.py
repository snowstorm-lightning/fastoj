from pydantic import field_validator
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
    JUDGE_ASYNC: bool = False  # Local dev defaults to inline judging; Docker enables queue mode.

    # Queue
    JUDGE_QUEUE_NAME: str = "judge_tasks"
    JUDGE_STREAM_NAME: str = "judge:tasks"
    JUDGE_CONSUMER_GROUP: str = "judge-workers"
    JUDGE_DEAD_LETTER_STREAM: str = "judge:dead-letter"
    JUDGE_STATUS_CHANNEL: str = "judge:status"
    JUDGE_TASK_MAX_RETRIES: int = 3
    JUDGE_PENDING_IDLE_MS: int = 30000

    # Sandbox safety
    FASTOJ_ALLOW_UNSAFE_LOCAL_EXECUTION: bool = False
    JUDGE_MAX_OUTPUT_BYTES: int = 65536

    # AI
    AI_PROVIDER: str = "disabled"
    AI_BASE_URL: str = "http://localhost:8080/v1"
    AI_API_KEY: str = "sk-no-key-required"
    AI_MODEL: str = "qwen2.5-coder-3b-instruct"
    AI_DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    AI_DEEPSEEK_API_KEY: str = ""
    AI_DEEPSEEK_MODEL: str = "deepseek-v4-flash"
    AI_QWEN_BASE_URL: str = "http://host.docker.internal:8080/v1"
    AI_QWEN_API_KEY: str = "sk-no-key-required"
    AI_QWEN_MODEL: str = "qwen2.5-coder-3b-instruct"
    AI_TIMEOUT_SECONDS: int = 60
    AI_MAX_OUTPUT_TOKENS: int = 1200

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Accept common deployment words from ambient DEBUG env vars."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production", "false", "0", "no", "off"}:
                return False
            if normalized in {"debug", "dev", "development", "true", "1", "yes", "on"}:
                return True
        return value


settings = Settings()
