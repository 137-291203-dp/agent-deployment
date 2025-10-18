"""
Configuration management for Agent LLM Deployment System.

This module handles loading configuration from environment variables
using Pydantic settings with proper validation and defaults.
"""

import os
import secrets
from typing import List, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMSettings(BaseSettings):
    """LLM provider configuration."""
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None)
    
    # Free providers
    groq_api_key: Optional[str] = Field(default=None)
    huggingface_api_key: Optional[str] = Field(default=None)
    
    # AIPipe (legacy)
    aipipe_key: Optional[str] = Field(default=None)
    aipipe_base_url: str = "https://aipipe.org/openrouter/v1"
    aipipe_model: str = "anthropic/claude-sonnet-4"
    
    # Model settings
    model_temperature: float = 0.1
    max_model_retries: int = 3
    request_timeout_seconds: int = 180
    
    class Config:
        extra = "ignore"


class GitHubSettings(BaseSettings):
    """GitHub integration configuration."""
    
    personal_access_token: Optional[str] = Field(default=None)
    enable_github_integration: bool = True
    repository_name_prefix: str = "ai-agent-"
    enable_pages_by_default: bool = True
    pages_polling_timeout_seconds: int = 120
    pages_polling_interval_seconds: int = 5
    
    class Config:
        extra = "ignore"


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # Application metadata
    APPLICATION_NAME: str = "Agent LLM Deployment System"
    APPLICATION_VERSION: str = "1.0.0"

    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False

    # Security
    SECRET_KEY: str = Field(default=os.getenv("SECRET_KEY", secrets.token_urlsafe(32)))

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Database
    DATABASE_URL: str = "sqlite:///data/deployment.db"

    # Hugging Face Integration
    HF_TOKEN: Optional[str] = Field(default=os.getenv("HF_TOKEN"))
    DATABASE_ID: Optional[str] = Field(default=os.getenv("DATABASE_ID"))

    # LLM Configuration (will be moved to nested settings)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    AIPIPE_KEY: Optional[str] = Field(default=None)
    
    # Free LLM providers
    GROQ_API_KEY: Optional[str] = Field(default=None)
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None)
    
    # GitHub Configuration (will be moved to nested settings)
    GITHUB_TOKEN: Optional[str] = Field(default=None)
    ENABLE_GITHUB_INTEGRATION: bool = True
    
    # Nested settings (populated in model_validator)
    llm: Optional[LLMSettings] = Field(default=None)
    github: Optional[GitHubSettings] = Field(default=None)

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # File Upload
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB

    # Task Processing
    MAX_CONCURRENT_TASKS: int = 3
    TASK_TIMEOUT_MINUTES: int = 10
    AGENT_MAX_ITERATIONS: int = 50
    AGENT_ENABLE_VERBOSE_LOGGING: bool = True

    # Workspace
    TEMPORARY_WORKSPACE_DIRECTORY: str = "/tmp/agent-llm-deployment/workspaces"
    CLEANUP_WORKSPACES_ON_COMPLETION: bool = True

    # Redis (for Celery/Background Tasks)
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=os.getenv("SENTRY_DSN"))
    JAEGER_ENDPOINT: str = "http://localhost:14268/api/traces"

    # Deployment
    DEPLOYMENT_ENV: str = "development"

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v.upper()

    @model_validator(mode="after")
    def parse_cors_origins(self):
        """Parse CORS_ORIGINS from string to list."""
        if isinstance(self.CORS_ORIGINS, str):
            self.CORS_ORIGINS = [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self
    
    @model_validator(mode="after")
    def populate_nested_settings(self):
        """Populate nested settings from environment variables."""
        # Initialize LLM settings
        self.llm = LLMSettings(
            openai_api_key=self.OPENAI_API_KEY,
            anthropic_api_key=self.ANTHROPIC_API_KEY,
            aipipe_key=self.AIPIPE_KEY,
            groq_api_key=self.GROQ_API_KEY,
            huggingface_api_key=self.HUGGINGFACE_API_KEY
        )
        
        # Initialize GitHub settings
        self.github = GitHubSettings(
            personal_access_token=self.GITHUB_TOKEN,
            enable_github_integration=self.ENABLE_GITHUB_INTEGRATION
        )
        
        return self

    def get_database_url(self) -> str:
        """Ensure database directory exists and return URL."""
        if self.DATABASE_URL.startswith('sqlite:///'):
            db_path = self.DATABASE_URL.replace('sqlite:///', '')
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return self.DATABASE_URL


# Global settings instance (lazy-loaded)
_settings_instance: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton pattern)."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


# For backward compatibility
settings = get_settings()
