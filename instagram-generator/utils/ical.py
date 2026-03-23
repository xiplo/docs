"""iCal feed export — generate calendar feeds from scheduled content.

Exports:
  - CMS scheduled items as VEVENT entries
  - Content calendar as VEVENT entries
  - Standard .ics format (importable to Google Calendar, Outlook, etc.)
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)


class CalendarFeed:
    """Generate iCal feeds from scheduled content."""

    @classmethod
    def generate(cls, source: str = "all") -> str:
        """Generate an iCal feed.

        Sources: "cms", "calendar", "all"
        """
        events = []

        if source in ("cms", "all"):
            events.extend(cls._cms_events())

        if source in ("calendar", "all"):
            events.extend(cls._calendar_events())

        return cls._build_ical(events)

    @classmethod
    def export_file(cls, output_path: str = "", source: str = "all") -> Path:
        """Export iCal to a .ics file."""
        ical = cls.generate(source)
        if not output_path:
            output_path = str(Path(settings.content_output_dir) / "content_schedule.ics")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(ical)
        logger.info("ical.exported", path=str(path))
        return path

    @classmethod
    def _cms_events(cls) -> list[dict]:
        """Get events from CMS scheduled items."""
        events = []
        try:
            from cms.content_manager import ContentManager
            cm = ContentManager()
            for item in cm.list_scheduled():
                if item.scheduled_at:
                    platforms = ", ".join(item.target_platforms) if item.target_platforms else "instagram"
                    events.append({
                        "uid": f"cms-{item.id}@content-generator",
                        "summary": f"[{item.content_type.upper()}] {item.title or item.topic}",
                        "dtstart": cls._parse_dt(item.scheduled_at),
                        "description": (
                            f"Category: {item.category}\\n"
                            f"Platforms: {platforms}\\n"
                            f"Caption: {item.caption[:100]}"
                        ),
                        "status": "CONFIRMED",
                    })
        except Exception:
            pass
        return events

    @classmethod
    def _calendar_events(cls) -> list[dict]:
        """Get events from the content calendar."""
        events = []
        cal_file = Path(settings.content_output_dir) / "content_calendar.json"
        if not cal_file.exists():
            return events

        try:
            data = json.loads(cal_file.read_text())
            for entry in data:
                if entry.get("date"):
                    events.append({
                        "uid": f"cal-{entry.get('id', '')}@content-generator",
                        "summary": f"[{entry.get('content_type', 'post').upper()}] {entry.get('topic', '')}",
                        "dtstart": cls._parse_dt(entry["date"]),
                        "description": (
                            f"Category: {entry.get('category', '')}\\n"
                            f"Style: {entry.get('style_preset', '')}"
                        ),
                        "status": "TENTATIVE",
                    })
        except (json.JSONDecodeError, KeyError):
            pass

        return events

    @classmethod
    def _build_ical(cls, events: list[dict]) -> str:
        """Build an iCal string from events."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//ContentGenerator//ContentCMS//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Content Schedule",
            "X-WR-TIMEZONE:Asia/Tashkent",
        ]

        for event in events:
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{event.get('uid', '')}",
                f"DTSTART:{event.get('dtstart', '')}",
                f"SUMMARY:{event.get('summary', '')}",
                f"DESCRIPTION:{event.get('description', '')}",
                f"STATUS:{event.get('status', 'CONFIRMED')}",
                "DURATION:PT30M",
                "END:VEVENT",
            ])

        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    @classmethod
    def _parse_dt(cls, dt_str: str) -> str:
        """Parse datetime string to iCal format (YYYYMMDDTHHMMSS)."""
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.strftime("%Y%m%dT%H%M%S")
        except (ValueError, AttributeError):
            return datetime.now().strftime("%Y%m%dT%H%M%S")
