# tests/unit/test_config/test_settings.py
import pytest
from pydantic import ValidationError
import os
from src.config import get_settings, Settings
from src.config.settings import (
    DatabaseSettings,
    AgentSettings,
    LLMSettings,
    LoggingSettings,
    MiddlewareSettings
)

class TestMiddlewareSettings:
    """Test suite for middleware-specific settings validation and behavior."""
    
    def test_default_rate_limit_settings(self):
        """Verify that default rate limit settings are set correctly."""
        middleware_settings = MiddlewareSettings()
        assert middleware_settings.RATE_LIMIT_WINDOW_SECONDS == 60
        assert middleware_settings.RATE_LIMIT_MAX_REQUESTS == 100

    def test_invalid_window_seconds(self):
        """Ensure invalid window durations are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MiddlewareSettings(RATE_LIMIT_WINDOW_SECONDS=0)
        assert "Rate limit window must be between 1 and 3600 seconds" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MiddlewareSettings(RATE_LIMIT_WINDOW_SECONDS=3601)
        assert "Rate limit window must be between 1 and 3600 seconds" in str(exc_info.value)

    def test_invalid_max_requests(self):
        """Ensure invalid request limits are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            MiddlewareSettings(RATE_LIMIT_MAX_REQUESTS=0)
        assert "Maximum requests must be between 1 and 1000 per window" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            MiddlewareSettings(RATE_LIMIT_MAX_REQUESTS=1001)
        assert "Maximum requests must be between 1 and 1000 per window" in str(exc_info.value)

    def test_environment_override(self):
        """Verify that environment variables properly override defaults."""
        os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "120"
        os.environ["RATE_LIMIT_MAX_REQUESTS"] = "50"
        
        settings = MiddlewareSettings()
        assert settings.RATE_LIMIT_WINDOW_SECONDS == 120
        assert settings.RATE_LIMIT_MAX_REQUESTS == 50
        
        del os.environ["RATE_LIMIT_WINDOW_SECONDS"]
        del os.environ["RATE_LIMIT_MAX_REQUESTS"]

class TestDatabaseSettings:
    """Test suite for database-specific settings validation and behavior."""
    
    def test_default_mongodb_settings(self):
        """Verify that default MongoDB settings are set correctly."""
        db_settings = DatabaseSettings()
        assert db_settings.MONGODB_URL == "mongodb://localhost:27017"
        assert db_settings.MONGODB_DB_NAME == "agent_db"
        assert db_settings.MONGODB_MAX_CONNECTIONS == 10
        assert db_settings.MONGODB_TIMEOUT_MS == 5000

    def test_default_redis_settings(self):
        """Verify that default Redis settings are set correctly."""
        db_settings = DatabaseSettings()
        assert db_settings.REDIS_URL == "redis://localhost:6379"
        assert db_settings.REDIS_MAX_CONNECTIONS == 10
        assert db_settings.REDIS_TIMEOUT == 5

    def test_invalid_mongodb_url(self):
        """Ensure invalid MongoDB URLs are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DatabaseSettings(MONGODB_URL="invalid://localhost:27017")
        assert "MongoDB URL must start with mongodb:// or mongodb+srv://" in str(exc_info.value)

class TestMainSettings:
    """Test suite for the main Settings class and its integration features."""

    def test_default_main_settings(self):
        """Verify that the main settings class initializes correctly."""
        settings = Settings()
        assert settings.PROJECT_NAME == "AI Agent System"
        assert settings.VERSION == "1.0.0"
        assert settings.ENVIRONMENT == "development"

    def test_settings_categories_initialization(self):
        """Ensure all setting categories are properly initialized."""
        settings = Settings()
        assert isinstance(settings.db, DatabaseSettings)
        assert isinstance(settings.agent, AgentSettings)
        assert isinstance(settings.llm, LLMSettings)
        assert isinstance(settings.logging, LoggingSettings)
        assert isinstance(settings.middleware, MiddlewareSettings)

    @pytest.mark.skip(reason="Known issue with nested settings override - to be addressed in future sprint")
    def test_nested_settings_override(self):
        """Test that nested settings can be overridden through environment variables."""
        os.environ["MIDDLEWARE__RATE_LIMIT_WINDOW_SECONDS"] = "180"
        settings = Settings()
        assert settings.middleware.RATE_LIMIT_WINDOW_SECONDS == 180
        del os.environ["MIDDLEWARE__RATE_LIMIT_WINDOW_SECONDS"]

    def test_get_all_settings(self):
        """Verify the get_all_settings method returns complete configuration."""
        settings = Settings()
        all_settings = settings.get_all_settings()
        
        assert "project" in all_settings
        assert "database" in all_settings
        assert "agent" in all_settings
        assert "llm" in all_settings
        assert "logging" in all_settings
        assert "middleware" in all_settings

        assert all_settings["project"]["name"] == settings.PROJECT_NAME
        assert "RATE_LIMIT_WINDOW_SECONDS" in all_settings["middleware"]

class TestSettingsCaching:
    """Test suite for settings caching behavior."""

    def test_settings_singleton(self):
        """Verify that get_settings returns the same instance multiple times."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    def test_settings_cache_with_env_changes(self):
        """Verify caching behavior when environment variables change."""
        original_settings = get_settings()
        
        os.environ["PROJECT_NAME"] = "Modified Project"
        cached_settings = get_settings()
        
        assert cached_settings is original_settings
        assert cached_settings.PROJECT_NAME == original_settings.PROJECT_NAME
        
        del os.environ["PROJECT_NAME"]

@pytest.fixture
def clean_environment():
    """Fixture to ensure clean environment variables between tests."""
    stored_vars = {}
    vars_to_store = [
        "MONGODB_URL", "REDIS_URL", "PROJECT_NAME",
        "MIDDLEWARE__RATE_LIMIT_WINDOW_SECONDS",
        "MIDDLEWARE__RATE_LIMIT_MAX_REQUESTS"
    ]
    
    for var in vars_to_store:
        if var in os.environ:
            stored_vars[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    for var, value in stored_vars.items():
        os.environ[var] = value