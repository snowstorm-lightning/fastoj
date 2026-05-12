"""Tests for configuration settings."""

import pytest


class TestSettings:
    """Test cases for Settings configuration."""

    def test_settings_can_be_instantiated(self):
        """Test that Settings can be instantiated."""
        from backend.core.config import Settings
        settings = Settings()
        assert settings.APP_NAME == "FastOJ"
        assert settings.APP_VERSION == "1.0.0"

    def test_judge_queue_name(self):
        """Test judge queue name configuration."""
        from backend.core.config import Settings
        settings = Settings()
        assert settings.JUDGE_QUEUE_NAME == "judge_tasks"

    def test_cors_origins_list(self):
        """Test CORS origins is a list."""
        from backend.core.config import Settings
        settings = Settings()
        assert isinstance(settings.CORS_ORIGINS, list)
        assert "http://localhost:3000" in settings.CORS_ORIGINS

    def test_security_settings(self):
        """Test security-related settings."""
        from backend.core.config import Settings
        settings = Settings()
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) > 0
        assert settings.ALGORITHM == "HS256"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS == 7

    def test_default_limits(self):
        """Test default judge limits."""
        from backend.core.config import Settings
        settings = Settings()
        assert settings.DEFAULT_TIME_LIMIT == 1000
        assert settings.DEFAULT_MEMORY_LIMIT == 256

    def test_database_url_uses_postgresql(self):
        """Test database URL uses postgresql."""
        from backend.core.config import Settings
        settings = Settings()
        assert "postgresql" in settings.DATABASE_URL

    def test_redis_url_uses_redis_protocol(self):
        """Test Redis URL uses redis:// protocol."""
        from backend.core.config import Settings
        settings = Settings()
        assert settings.REDIS_URL.startswith("redis://")
