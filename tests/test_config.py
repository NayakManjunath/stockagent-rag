"""Tests for application configuration."""

from stockagent.config import Settings


def test_default_configuration() -> None:
    """Verify that default configuration values are loaded correctly."""

    settings = Settings()

    assert settings.app_env == "development"
    assert settings.log_level == "INFO"
    assert settings.llm_provider == "openai"