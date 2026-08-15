"""Application entry point for the StockAgent RAG project."""

import logging

from stockagent.config import Settings
from stockagent.logging_config import configure_logging


def main() -> None:
    """Run the StockAgent RAG application."""

    settings = Settings()

    configure_logging(settings.log_level)

    logger = logging.getLogger(__name__)

    logger.info("StockAgent RAG application started.")
    logger.info("Environment: %s", settings.app_env)
    logger.info("LLM Provider: %s", settings.llm_provider)


if __name__ == "__main__":
    main()