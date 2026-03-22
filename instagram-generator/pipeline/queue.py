"""Content Queue — managed queue for scheduled content publication.

Features:
  - Priority-based queue (high priority posts first)
  - Persistent storage (survives restarts)
  - Deduplication by topic
  - Status tracking (queued → processing → published → failed)
  - Retry logic for failed posts
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

import structlog

from config import settings

logger = structlog.get_logger(__name__)

QueueStatus = Literal["queued", "processing", "published", "failed", "cancelled"]

QUEUE_FILE = Path(settings.content_output_dir) / settings.queue_file


@dataclass
class QueueItem:
    """A single item in the content queue."""

    id: str = ""
    topic: str = ""
    category: str = ""
    content_type: str = "reel"
    style_preset: str = "photorealistic"
    duration: str = "5"
    scheduled_time: str = ""  # ISO format or empty for ASAP
    priority: int = 5  # 1=lowest, 10=highest
    status: QueueStatus = "queued"
    retry_count: int = 0
    max_retries: int = 3
    media_id: str = ""
    error: str = ""
    created_at: str = ""
    updated_at: str = ""
    brief_path: str = ""  # Path to saved creative brief

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


class ContentQueue:
    """Priority queue for content publication."""

    def __init__(self) -> None:
        self._items: list[QueueItem] = []
        self._load()

    # ------------------------------------------------------------------
    # Queue operations
    # ------------------------------------------------------------------

    def enqueue(
        self,
        topic: str,
        category: str,
        content_type: str = "reel",
        *,
        style_preset: str = "photorealistic",
        duration: str = "5",
        scheduled_time: str = "",
        priority: int = 5,
    ) -> QueueItem:
        """Add a new item to the queue."""
        if len(self._items) >= settings.queue_max_size:
            # Remove oldest completed/failed items
            self._items = [
                i for i in self._items
                if i.status in ("queued", "processing")
            ]

        # Deduplication check
        for item in self._items:
            if (
                item.topic == topic
                and item.status == "queued"
                and item.category == category
            ):
                logger.warning("queue.duplicate", topic=topic)
                return item

        item = QueueItem(
            topic=topic,
            category=category,
            content_type=content_type,
            style_preset=style_preset,
            duration=duration,
            scheduled_time=scheduled_time,
            priority=priority,
        )
        self._items.append(item)
        self._save()
        logger.info("queue.enqueued", id=item.id, topic=topic, priority=priority)
        return item

    def dequeue(self) -> QueueItem | None:
        """Get the highest-priority queued item ready for processing."""
        now = datetime.now().isoformat()

        ready = [
            i for i in self._items
            if i.status == "queued"
            and (not i.scheduled_time or i.scheduled_time <= now)
        ]

        if not ready:
            return None

        # Sort by priority (highest first), then by created_at (oldest first)
        ready.sort(key=lambda x: (-x.priority, x.created_at))
        item = ready[0]
        item.status = "processing"
        item.updated_at = datetime.now().isoformat()
        self._save()
        logger.info("queue.dequeued", id=item.id, topic=item.topic)
        return item

    def mark_published(self, item_id: str, media_id: str = "") -> None:
        item = self._find(item_id)
        if item:
            item.status = "published"
            item.media_id = media_id
            item.updated_at = datetime.now().isoformat()
            self._save()
            logger.info("queue.published", id=item_id, media_id=media_id)

    def mark_failed(self, item_id: str, error: str = "") -> None:
        item = self._find(item_id)
        if item:
            item.retry_count += 1
            if item.retry_count < item.max_retries:
                item.status = "queued"  # Re-queue for retry
                item.priority = max(1, item.priority - 1)  # Lower priority on retry
            else:
                item.status = "failed"
            item.error = error
            item.updated_at = datetime.now().isoformat()
            self._save()
            logger.warning(
                "queue.failed",
                id=item_id,
                retry=item.retry_count,
                error=error[:100],
            )

    def cancel(self, item_id: str) -> bool:
        item = self._find(item_id)
        if item and item.status in ("queued", "processing"):
            item.status = "cancelled"
            item.updated_at = datetime.now().isoformat()
            self._save()
            return True
        return False

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def enqueue_from_calendar(self, slots: list) -> list[QueueItem]:
        """Enqueue all slots from a content calendar."""
        items = []
        for slot in slots:
            item = self.enqueue(
                topic=slot.topic,
                category=slot.category,
                content_type=slot.content_type,
                style_preset=slot.style_preset,
                duration=slot.duration,
                scheduled_time=f"{slot.day}T{slot.time}:00",
                priority=slot.priority,
            )
            items.append(item)
        return items

    def get_pending_count(self) -> int:
        return sum(1 for i in self._items if i.status == "queued")

    def get_stats(self) -> dict[str, int]:
        stats: dict[str, int] = {}
        for item in self._items:
            stats[item.status] = stats.get(item.status, 0) + 1
        return stats

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self, limit: int = 20) -> str:
        lines = [
            "=" * 70,
            "  Content Queue",
            "=" * 70,
        ]

        stats = self.get_stats()
        lines.append(f"  Total: {len(self._items)} | " + " | ".join(
            f"{k}: {v}" for k, v in sorted(stats.items())
        ))
        lines.append("")

        status_icons = {
            "queued": "[ ]",
            "processing": "[~]",
            "published": "[+]",
            "failed": "[!]",
            "cancelled": "[x]",
        }

        shown = self._items[-limit:]
        for item in shown:
            icon = status_icons.get(item.status, "[ ]")
            sched = item.scheduled_time[:16] if item.scheduled_time else "ASAP"
            lines.append(
                f"  {icon} P{item.priority} {sched:<17} "
                f"{item.content_type:<9} {item.category:<14} "
                f"{item.topic[:30]}"
            )

        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _find(self, item_id: str) -> QueueItem | None:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def _load(self) -> None:
        if QUEUE_FILE.exists():
            try:
                data = json.loads(QUEUE_FILE.read_text())
                self._items = [QueueItem(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._items = []

    def _save(self) -> None:
        QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(item) for item in self._items]
        QUEUE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
