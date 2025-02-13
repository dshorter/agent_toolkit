# src/config/settings.py
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
import os
from functools import lru_cache

class DatabaseSettings(BaseSettings):
    """Database configuration settings including both MongoDB and Redis."""
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection string. Supports replica sets and authentication."
    )
    MONGODB_DB_NAME: str = Field(
        default="agent_db",
        description="Name of the MongoDB database to use"
    )
    MONGODB_MAX_CONNECTIONS: int = Field(
        default=10,
        description="Maximum number of MongoDB connections to maintain"
    )
    MONGODB_TIMEOUT_MS: int = Field(
        default=5000,
        description="MongoDB operation timeout in milliseconds"
    )
    
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection string"
    )
    REDIS_MAX_CONNECTIONS: int = Field(
        default=10,
        description="Maximum number of Redis connections in the pool"
    )
    REDIS_TIMEOUT: int = Field(
        default=5,
        description="Redis operation timeout in seconds"
    )

    @field_validator("MONGODB_URL")
    def validate_mongodb_url(cls, v: str) -> str:
        if not v.startswith(("mongodb://", "mongodb+srv://")):
            raise ValueError("MongoDB URL must start with mongodb:// or mongodb+srv://")
        return v

    model_config = SettingsConfigDict(
        extra="allow",
        env_nested_delimiter="__"
    )

class AgentSettings(BaseSettings):
    """Agent-specific configuration settings."""
    AGENT_DEFAULT_TIMEOUT: int = Field(
        default=300,
        description="Default timeout for agent operations in seconds"
    )
    AGENT_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed operations"
    )
    AGENT_MEMORY_TTL: int = Field(
        default=3600,
        description="Time-to-live for agent memory entries in seconds"
    )
    AGENT_MAX_CONCURRENT_TASKS: int = Field(
        default=5,
        description="Maximum number of tasks an agent can process concurrently"
    )
    
    @field_validator("AGENT_DEFAULT_TIMEOUT")
    def validate_timeout(cls, v: int) -> int:
        if v < 1 or v > 3600:
            raise ValueError("Agent timeout must be between 1 and 3600 seconds")
        return v

    model_config = SettingsConfigDict(
        extra="allow",
        env_nested_delimiter="__"
    )

class LLMSettings(BaseSettings):
    """Language Model configuration settings."""
    LLM_MODEL_NAME: str = Field(
        default="mistral-7b",
        description="Name of the language model to use"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.7,
        description="Temperature parameter for text generation"
    )
    LLM_MAX_TOKENS: int = Field(
        default=2000,
        description="Maximum number of tokens in model responses"
    )
    LLM_CONTEXT_WINDOW: int = Field(
        default=4096,
        description="Maximum context window size in tokens"
    )
    
    @field_validator("LLM_TEMPERATURE")
    def validate_temperature(cls, v: float) -> float:
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v

    model_config = SettingsConfigDict(
        extra="allow",
        env_nested_delimiter="__"
    )

class LoggingSettings(BaseSettings):
    """Logging and monitoring configuration."""
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Minimum log level to record"
    )
    LOG_FORMAT: str = Field(
        default="json",
        description="Log output format (json or text)"
    )
    ENABLE_METRICS: bool = Field(
        default=True,
        description="Whether to collect and expose metrics"
    )
    METRICS_PORT: int = Field(
        default=8000,
        description="Port to expose metrics on"
    )
    
    @field_validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    model_config = SettingsConfigDict(
        extra="allow",
        env_nested_delimiter="__"
    )

class MiddlewareSettings(BaseSettings):
    """Configuration settings for API middleware components."""
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default=60,
        description="Duration of the rate limiting window in seconds"
    )
    RATE_LIMIT_MAX_REQUESTS: int = Field(
        default=100,
        description="Maximum number of requests allowed within the window"
    )
    
    @field_validator("RATE_LIMIT_WINDOW_SECONDS")
    def validate_window_seconds(cls, v: int) -> int:
        if v < 1 or v > 3600:
            raise ValueError("Rate limit window must be between 1 and 3600 seconds")
        return v
    
    @field_validator("RATE_LIMIT_MAX_REQUESTS")
    def validate_max_requests(cls, v: int) -> int:
        if v < 1 or v > 1000:
            raise ValueError("Maximum requests must be between 1 and 1000 per window")
        return v

    model_config = SettingsConfigDict(
        extra="allow",
        env_nested_delimiter="__"
    )

class Settings(BaseSettings):
    """Main configuration class combining all setting categories."""
    PROJECT_NAME: str = Field(
        default="AI Agent System",
        description="Name of the project"
    )
    VERSION: str = Field(
        default="1.0.0",
        description="Project version"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Deployment environment"
    )
    
    # Include all setting categories
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    agent: AgentSettings = Field(default_factory=AgentSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    middleware: MiddlewareSettings = Field(default_factory=MiddlewareSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="allow",
        validate_assignment=True,
        case_sensitive=True
    )

    def get_all_settings(self) -> Dict[str, Any]:
        """Returns all settings as a dictionary for logging/debugging"""
        return {
            "project": {
                "name": self.PROJECT_NAME,
                "version": self.VERSION,
                "environment": self.ENVIRONMENT
            },
            "database": self.db.model_dump(),
            "agent": self.agent.model_dump(),
            "llm": self.llm.model_dump(),
            "logging": self.logging.model_dump(),
            "middleware": self.middleware.model_dump()
        }

@lru_cache()
def get_settings() -> Settings:
    """Creates and returns a cached instance of settings."""
    return Settings()