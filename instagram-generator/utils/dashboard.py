"""Live system dashboard — rich CLI overview of all subsystems.

Displays in one view:
  - Pipeline status (published/failed/blocked)
  - Queue depth
  - Circuit breaker states
  - Rate limiter usage
  - Token health
  - Notification channels
  - Active plugins
  - Recent metrics
"""

from __future__ import annotations

from datetime import datetime

import structlog

logger = structlog.get_logger(__name__)


class Dashboard:
    """Aggregate system status into a unified display."""

    @classmethod
    def render(cls) -> str:
        """Render the full system dashboard."""
        lines = [
            "",
            "=" * 70,
            "  INSTAGRAM CONTENT GENERATOR — System Dashboard",
            f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
        ]

        lines.extend(cls._queue_section())
        lines.extend(cls._circuit_breakers_section())
        lines.extend(cls._rate_limiters_section())
        lines.extend(cls._token_section())
        lines.extend(cls._notifications_section())
        lines.extend(cls._plugins_section())
        lines.extend(cls._metrics_section())
        lines.extend(cls._recent_history_section())

        lines.append("=" * 70)
        return "\n".join(lines)

    @classmethod
    def _queue_section(cls) -> list[str]:
        lines = ["\n  QUEUE"]
        try:
            from pipeline.queue import ContentQueue
            q = ContentQueue()
            stats = q.get_stats()
            for key, val in stats.items():
                lines.append(f"    {key:<20} {val}")
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines

    @classmethod
    def _circuit_breakers_section(cls) -> list[str]:
        lines = ["\n  CIRCUIT BREAKERS"]
        try:
            from utils.circuit_breaker import CIRCUIT_BREAKERS
            for name, cb in CIRCUIT_BREAKERS.items():
                s = cb.get_status()
                state = s["state"]
                indicator = "[OK]" if state == "closed" else "[!!]" if state == "open" else "[??]"
                lines.append(
                    f"    {indicator} {name:<15} {state:<12} "
                    f"failures={s['failures']}"
                )
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines

    @classmethod
    def _rate_limiters_section(cls) -> list[str]:
        lines = ["\n  RATE LIMITERS"]
        try:
            from utils.rate_limiter import RATE_LIMITERS
            for name, rl in RATE_LIMITERS.items():
                lines.append(
                    f"    {name:<15} {rl.rate:.2f} req/s  burst={rl.capacity}"
                )
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines

    @classmethod
    def _token_section(cls) -> list[str]:
        lines = ["\n  INSTAGRAM TOKEN"]
        try:
            from utils.token_refresh import TokenRefresher
            tr = TokenRefresher()
            status = tr.get_status()
            configured = "Yes" if status["configured"] else "No"
            lines.append(f"    Configured:    {configured}")
            lines.append(f"    Expires:       {status['expires_at']}")
            lines.append(f"    Days left:     {status['days_remaining']}")
            if status["needs_refresh"]:
                lines.append("    [!!] Token needs refresh!")
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines

    @classmethod
    def _notifications_section(cls) -> list[str]:
        lines = ["\n  NOTIFICATIONS"]
        try:
            from notifications import NotificationManager
            nm = NotificationManager()
            tg = "ON" if nm.telegram_enabled else "OFF"
            wh = "ON" if nm.webhook_enabled else "OFF"
            lines.append(f"    Telegram:      {tg}")
            lines.append(f"    Webhook:       {wh}")
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines

    @classmethod
    def _plugins_section(cls) -> list[str]:
        lines = ["\n  PLUGINS"]
        try:
            from plugins import plugin_registry
            plugins = plugin_registry.get_plugins()
            if plugins:
                for name, meta in plugins.items():
                    v = meta.get("version", "?")
                    lines.append(f"    {name:<20} v{v}")
            else:
                lines.append("    No plugins loaded.")

            hooks = plugin_registry.get_hooks_count()
            if hooks:
                total = sum(hooks.values())
                lines.append(f"    {total} hook(s) registered")
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines

    @classmethod
    def _metrics_section(cls) -> list[str]:
        lines = ["\n  METRICS (top counters)"]
        try:
            from utils.metrics import metrics
            data = metrics.get_all()
            counters = sorted(
                data["counters"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:5]
            for key, val in counters:
                lines.append(f"    {key:<40} {val:.0f}")
            if not counters:
                lines.append("    No metrics collected yet.")
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines

    @classmethod
    def _recent_history_section(cls) -> list[str]:
        lines = ["\n  RECENT POSTS (last 5)"]
        try:
            import json
            from pathlib import Path
            from config import settings

            history_file = Path(settings.content_output_dir) / "post_history.json"
            if history_file.exists():
                history = json.loads(history_file.read_text())
                for entry in history[-5:]:
                    status = entry.get("status", "?")
                    icon = "[+]" if status == "published" else "[-]"
                    ts = entry.get("timestamp", "")[:16]
                    tmpl = entry.get("template", "")[:30]
                    lines.append(f"    {icon} {ts}  {tmpl}")
            else:
                lines.append("    No post history yet.")
        except Exception as exc:
            lines.append(f"    Error: {exc}")
        return lines
