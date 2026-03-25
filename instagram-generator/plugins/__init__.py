"""Plugin system — extensible hooks for the content pipeline.

Plugins can hook into pipeline events:
  - on_pre_generate  — Before content generation starts
  - on_post_generate — After content is generated (before publish)
  - on_published     — After content is published to Instagram
  - on_failed        — When pipeline fails
  - on_moderation    — When moderation checks content

Plugins are Python modules in the `plugins/` directory that define
a `register(registry)` function.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Callable

import structlog

logger = structlog.get_logger(__name__)

# Hook event types
HOOK_EVENTS = (
    "on_pre_generate",
    "on_post_generate",
    "on_published",
    "on_failed",
    "on_moderation",
    "on_schedule",
    "on_queue_add",
)


class PluginRegistry:
    """Registry for pipeline plugins."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._hooks: dict[str, list[Callable]] = {event: [] for event in HOOK_EVENTS}
        self._plugins: dict[str, dict] = {}

    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a callback for a pipeline event."""
        if event not in self._hooks:
            logger.warning("plugin.unknown_hook", hook_name=event)
            return
        self._hooks[event].append(callback)

    def register_plugin(self, name: str, metadata: dict | None = None) -> None:
        """Register a plugin with metadata."""
        self._plugins[name] = metadata or {}
        logger.info("plugin.registered", name=name)

    async def emit(self, event: str, **kwargs) -> list[Any]:
        """Emit an event to all registered hooks."""
        results = []
        for hook in self._hooks.get(event, []):
            try:
                result = hook(**kwargs)
                # Support both sync and async hooks
                if hasattr(result, "__await__"):
                    result = await result
                results.append(result)
            except Exception as exc:
                logger.warning(
                    "plugin.hook_error",
                    hook_event=event,
                    error=str(exc),
                )
        return results

    def load_plugins(self, plugin_dir: str = "plugins") -> int:
        """Discover and load plugins from the plugins/ directory."""
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return 0

        # Add plugin dir to path
        sys.path.insert(0, str(plugin_path.parent))

        loaded = 0
        for py_file in plugin_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue

            module_name = f"{plugin_dir}.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, "register"):
                    module.register(self)
                    loaded += 1
                    logger.info("plugin.loaded", module=module_name)
            except Exception as exc:
                logger.error("plugin.load_error", module=module_name, error=str(exc))

        return loaded

    def get_plugins(self) -> dict[str, dict]:
        """Get all registered plugins."""
        return dict(self._plugins)

    def get_hooks_count(self) -> dict[str, int]:
        """Get hook registration counts."""
        return {event: len(hooks) for event, hooks in self._hooks.items() if hooks}

    def display(self) -> str:
        """Display plugin status."""
        lines = [
            "=" * 55,
            "  Plugin System",
            "=" * 55,
        ]

        if self._plugins:
            lines.append(f"\n  Plugins ({len(self._plugins)}):")
            for name, meta in self._plugins.items():
                desc = meta.get("description", "")
                version = meta.get("version", "")
                lines.append(f"    {name:<20} v{version}  {desc}")
        else:
            lines.append("  No plugins loaded.")

        hook_counts = self.get_hooks_count()
        if hook_counts:
            lines.append(f"\n  Active hooks:")
            for event, count in hook_counts.items():
                lines.append(f"    {event:<20} {count} handler(s)")

        lines.append("=" * 55)
        return "\n".join(lines)

    def reset(self) -> None:
        """Reset registry (for testing)."""
        self._hooks = {event: [] for event in HOOK_EVENTS}
        self._plugins.clear()


# Singleton
plugin_registry = PluginRegistry()
