"""Logging configuration for the StockAgent RAG application."""

import logging


def configure_logging(log_level: str) -> None:
    """Configure application-wide logging."""

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )