# tests/test_config/test_settings.py
import pytest
from pydantic import ValidationError  
import os
from src.config import get_settings, Settings
from src.config.settings import (
    DatabaseSettings,
    AgentSettings,
    LLMSettings,
    LoggingSettings
)

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

    def test_environment_override(self):
        """Verify that environment variables properly override defaults."""
        test_url = "mongodb://testhost:27017"
        os.environ["MONGODB_URL"] = test_url
        db_settings = DatabaseSettings()
        assert db_settings.MONGODB_URL == test_url
        del os.environ["MONGODB_URL"]

class TestAgentSettings:
    """Test suite for agent-specific settings validation and behavior."""

    def test_default_agent_settings(self):
        """Verify that default agent settings are set correctly."""
        agent_settings = AgentSettings()
        assert agent_settings.AGENT_DEFAULT_TIMEOUT == 300
        assert agent_settings.AGENT_MAX_RETRIES == 3
        assert agent_settings.AGENT_MEMORY_TTL == 3600
        assert agent_settings.AGENT_MAX_CONCURRENT_TASKS == 5

    def test_invalid_timeout(self):
        """Ensure invalid timeout values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            AgentSettings(AGENT_DEFAULT_TIMEOUT=0)
        assert "Agent timeout must be between 1 and 3600 seconds" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            AgentSettings(AGENT_DEFAULT_TIMEOUT=3601)
        assert "Agent timeout must be between 1 and 3600 seconds" in str(exc_info.value)

class TestLLMSettings:
    """Test suite for Language Model settings validation and behavior."""

    def test_default_llm_settings(self):
        """Verify that default LLM settings are set correctly."""
        llm_settings = LLMSettings()
        assert llm_settings.LLM_MODEL_NAME == "mistral-7b"
        assert llm_settings.LLM_TEMPERATURE == 0.7
        assert llm_settings.LLM_MAX_TOKENS == 2000
        assert llm_settings.LLM_CONTEXT_WINDOW == 4096

    def test_invalid_temperature(self):
        """Ensure invalid temperature values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LLMSettings(LLM_TEMPERATURE=-0.1)
        assert "Temperature must be between 0.0 and 2.0" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            LLMSettings(LLM_TEMPERATURE=2.1)
        assert "Temperature must be between 0.0 and 2.0" in str(exc_info.value)

class TestLoggingSettings:
    """Test suite for logging and monitoring settings validation and behavior."""

    def test_default_logging_settings(self):
        """Verify that default logging settings are set correctly."""
        logging_settings = LoggingSettings()
        assert logging_settings.LOG_LEVEL == "INFO"
        assert logging_settings.LOG_FORMAT == "json"
        assert logging_settings.ENABLE_METRICS is True
        assert logging_settings.METRICS_PORT == 8000

    def test_invalid_log_level(self):
        """Ensure invalid log levels are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LoggingSettings(LOG_LEVEL="INVALID")
        assert "Log level must be one of" in str(exc_info.value)

    def test_log_level_case_insensitive(self):
        """Verify that log level settings are case-insensitive."""
        logging_settings = LoggingSettings(LOG_LEVEL="debug")
        assert logging_settings.LOG_LEVEL == "DEBUG"

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

    def test_get_all_settings(self):
        """Verify the get_all_settings method returns complete configuration."""
        settings = Settings()
        all_settings = settings.get_all_settings()
        
        assert "project" in all_settings
        assert "database" in all_settings
        assert "agent" in all_settings
        assert "llm" in all_settings
        assert "logging" in all_settings

        assert all_settings["project"]["name"] == settings.PROJECT_NAME
        assert all_settings["database"]["MONGODB_URL"] == settings.db.MONGODB_URL

class TestSettingsCaching:
    """Test suite for settings caching behavior."""

    def test_settings_singleton(self):
        """Verify that get_settings returns the same instance multiple times."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2  # Check object identity

    def test_settings_cache_with_env_changes(self):
        """Verify caching behavior when environment variables change."""
        original_settings = get_settings()
        
        # Change environment and get settings again
        os.environ["PROJECT_NAME"] = "Modified Project"
        cached_settings = get_settings()
        
        # Should return cached instance, ignoring environment change
        assert cached_settings is original_settings
        assert cached_settings.PROJECT_NAME == original_settings.PROJECT_NAME
        
        # Clean up
        del os.environ["PROJECT_NAME"]

@pytest.fixture
def clean_environment():
    """Fixture to ensure clean environment variables between tests."""
    # Store existing environment variables we might modify
    stored_vars = {}
    vars_to_store = [
        "MONGODB_URL", "REDIS_URL", "PROJECT_NAME",
        "AGENT_DEFAULT_TIMEOUT", "LLM_MODEL_NAME", "LOG_LEVEL"
    ]
    
    for var in vars_to_store:
        if var in os.environ:
            stored_vars[var] = os.environ[var]
            del os.environ[var]
    
    yield
    
    # Restore environment variables
    for var, value in stored_vars.items():
        os.environ[var] = value  
        
        
        