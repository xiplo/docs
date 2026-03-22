"""Content Calendar — visual calendar management and export."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import structlog

from config import settings
from .engine import ContentSlot

logger = structlog.get_logger(__name__)

CALENDAR_FILE = Path(settings.content_output_dir) / "content_calendar.json"


class ContentCalendar:
    """Manages a persistent content calendar."""

    def __init__(self) -> None:
        self._slots: list[ContentSlot] = []

    def load(self) -> None:
        if CALENDAR_FILE.exists():
            data = json.loads(CALENDAR_FILE.read_text())
            self._slots = [ContentSlot(**s) for s in data]
            logger.info("calendar.loaded", count=len(self._slots))

    def save(self) -> None:
        CALENDAR_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [
            {
                "day": s.day,
                "time": s.time,
                "content_type": s.content_type,
                "category": s.category,
                "topic": s.topic,
                "style_preset": s.style_preset,
                "duration": s.duration,
                "target_segment": s.target_segment,
                "priority": s.priority,
            }
            for s in self._slots
        ]
        CALENDAR_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("calendar.saved", count=len(self._slots))

    def set_slots(self, slots: list[ContentSlot]) -> None:
        self._slots = slots

    def get_slots_for_day(self, day: str) -> list[ContentSlot]:
        return [s for s in self._slots if s.day == day]

    def get_next_slot(self) -> ContentSlot | None:
        now = datetime.now()
        today = now.date().isoformat()
        current_time = now.strftime("%H:%M")

        for slot in sorted(self._slots, key=lambda s: (s.day, s.time)):
            if slot.day > today:
                return slot
            if slot.day == today and slot.time > current_time:
                return slot
        return None

    def display(self) -> str:
        """Generate a text-based calendar view."""
        if not self._slots:
            return "No content planned."

        lines = [
            "=" * 70,
            "  Content Calendar",
            "=" * 70,
        ]

        # Group by day
        days: dict[str, list[ContentSlot]] = {}
        for slot in sorted(self._slots, key=lambda s: (s.day, s.time)):
            days.setdefault(slot.day, []).append(slot)

        for day, slots in days.items():
            dt = datetime.fromisoformat(day)
            day_name = dt.strftime("%A")
            lines.append(f"\n  {day} ({day_name})")
            lines.append(f"  {'-' * 60}")

            for slot in slots:
                lines.append(
                    f"    {slot.time}  "
                    f"[{slot.content_type:<9}] "
                    f"{slot.category:<14} "
                    f"| {slot.topic[:35]}"
                )

        lines.append("\n" + "=" * 70)
        lines.append(f"  Total: {len(self._slots)} posts planned")
        lines.append("=" * 70)

        return "\n".join(lines)
