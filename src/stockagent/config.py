"""Application configuration management."""

import os

from dotenv import load_dotenv


load_dotenv()


class Settings:
    """Store and validate application configuration."""

    ALLOWED_ENVIRONMENTS = {"development", "testing", "production"}
    ALLOWED_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    ALLOWED_LLM_PROVIDERS = {"openai", "google"}

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "development")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai")
        self.llm_model = os.getenv("LLM_MODEL", "")

        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")

        self.validate()

    def validate(self) -> None:
        """Validate application configuration values."""

        if self.app_env not in self.ALLOWED_ENVIRONMENTS:
            raise ValueError(
                f"Invalid APP_ENV: {self.app_env}. "
                f"Expected one of: {sorted(self.ALLOWED_ENVIRONMENTS)}"
            )

        if self.log_level not in self.ALLOWED_LOG_LEVELS:
            raise ValueError(
                f"Invalid LOG_LEVEL: {self.log_level}. "
                f"Expected one of: {sorted(self.ALLOWED_LOG_LEVELS)}"
            )

        if self.llm_provider not in self.ALLOWED_LLM_PROVIDERS:
            raise ValueError(
                f"Invalid LLM_PROVIDER: {self.llm_provider}. "
                f"Expected one of: {sorted(self.ALLOWED_LLM_PROVIDERS)}"
            )