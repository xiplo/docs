"""Example plugin — logging hooks for pipeline events.

To create your own plugin:
  1. Create a .py file in the plugins/ directory
  2. Define a `register(registry)` function
  3. Register hooks for the events you care about
"""

from __future__ import annotations

import structlog

logger = structlog.get_logger("plugin.example_logger")


def register(registry) -> None:
    """Register this plugin with the pipeline."""
    registry.register_plugin(
        "example_logger",
        {
            "version": "1.0.0",
            "description": "Logs pipeline events for debugging",
            "author": "Instagram Generator",
        },
    )

    registry.register_hook("on_pre_generate", on_pre_generate)
    registry.register_hook("on_published", on_published)
    registry.register_hook("on_failed", on_failed)


def on_pre_generate(**kwargs) -> None:
    logger.info(
        "plugin.pre_generate",
        content_type=kwargs.get("content_type", ""),
        topic=kwargs.get("topic", "")[:50],
    )


def on_published(**kwargs) -> None:
    logger.info(
        "plugin.published",
        media_id=kwargs.get("media_id", ""),
        content_type=kwargs.get("content_type", ""),
    )


def on_failed(**kwargs) -> None:
    logger.warning(
        "plugin.failed",
        error=kwargs.get("error", "")[:100],
        content_type=kwargs.get("content_type", ""),
    )
