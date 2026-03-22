"""Structured logging configuration.

Modes:
  - development: Colored console output (default)
  - production:  JSON lines to stdout (for log aggregation)

Set LOG_FORMAT=json for production mode.
"""

from __future__ import annotations

import logging
import os

import structlog


def setup_logging(log_level: str = "INFO", json_mode: bool | None = None) -> None:
    """Configure structlog for the application.

    Args:
        log_level: Python log level (DEBUG, INFO, WARNING, ERROR)
        json_mode: Force JSON output. If None, auto-detect from LOG_FORMAT env var.
    """
    if json_mode is None:
        json_mode = os.getenv("LOG_FORMAT", "").lower() == "json"

    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_mode:
        # Production: JSON lines
        renderer = structlog.processors.JSONRenderer(ensure_ascii=False)
        shared_processors.append(
            structlog.processors.format_exc_info,
        )
    else:
        # Development: colored console
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging for third-party libs
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )
