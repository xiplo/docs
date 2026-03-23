"""Content lifecycle manager — full CMS for social media content.

Lifecycle: draft → review → scheduled → publishing → published → archived

Each content item tracks:
  - All platform-specific versions (adapted captions, hashtags, media)
  - Approval status
  - Scheduling info
  - Publishing results per platform
  - Analytics links
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

CMS_FILE = Path(settings.content_output_dir) / "cms_content.json"


class ContentStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    ARCHIVED = "archived"


@dataclass
class PlatformVersion:
    """Platform-specific adaptation of content."""

    platform: str = ""
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    media_urls: list[str] = field(default_factory=list)
    media_paths: list[str] = field(default_factory=list)
    publish_id: str = ""
    publish_url: str = ""
    published_at: str = ""
    error: str = ""
    status: str = "pending"


@dataclass
class ContentItem:
    """A piece of content in the CMS."""

    id: str = ""
    title: str = ""
    topic: str = ""
    category: str = ""
    content_type: str = "reel"
    status: str = ContentStatus.DRAFT.value

    # Core content
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    voiceover_text: str = ""
    image_prompt: str = ""
    style_preset: str = "photorealistic"
    duration: str = "5"

    # Media
    media_paths: list[str] = field(default_factory=list)
    cdn_urls: list[str] = field(default_factory=list)
    thumbnail_path: str = ""

    # Platform versions
    platforms: dict[str, dict] = field(default_factory=dict)

    # Metadata
    campaign_id: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    quality_scores: dict = field(default_factory=dict)

    # Scheduling
    scheduled_at: str = ""
    target_platforms: list[str] = field(default_factory=list)

    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    published_at: str = ""
    archived_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:12]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


class ContentManager:
    """Full content lifecycle management."""

    def __init__(self) -> None:
        self._items: list[ContentItem] = []
        self._load()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, **kwargs) -> ContentItem:
        """Create a new content item in draft status."""
        item = ContentItem(**kwargs)
        item.status = ContentStatus.DRAFT.value
        self._items.append(item)
        self._save()
        logger.info("cms.created", id=item.id, title=item.title[:50])
        return item

    def get(self, item_id: str) -> ContentItem | None:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def update(self, item_id: str, **kwargs) -> ContentItem | None:
        item = self.get(item_id)
        if not item:
            return None
        for key, val in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, val)
        item.updated_at = datetime.now().isoformat()
        self._save()
        return item

    def delete(self, item_id: str) -> bool:
        item = self.get(item_id)
        if not item:
            return False
        self._items.remove(item)
        self._save()
        return True

    # ------------------------------------------------------------------
    # Lifecycle transitions
    # ------------------------------------------------------------------

    def submit_for_review(self, item_id: str) -> ContentItem | None:
        return self._transition(item_id, ContentStatus.REVIEW)

    def approve(self, item_id: str, notes: str = "") -> ContentItem | None:
        item = self._transition(item_id, ContentStatus.APPROVED)
        if item and notes:
            item.notes = notes
            self._save()
        return item

    def reject(self, item_id: str, notes: str = "") -> ContentItem | None:
        item = self._transition(item_id, ContentStatus.DRAFT)
        if item and notes:
            item.notes = f"Rejected: {notes}"
            self._save()
        return item

    def schedule(
        self, item_id: str, scheduled_at: str, platforms: list[str]
    ) -> ContentItem | None:
        item = self.get(item_id)
        if not item:
            return None
        item.status = ContentStatus.SCHEDULED.value
        item.scheduled_at = scheduled_at
        item.target_platforms = platforms
        item.updated_at = datetime.now().isoformat()
        self._save()
        return item

    def mark_publishing(self, item_id: str) -> ContentItem | None:
        return self._transition(item_id, ContentStatus.PUBLISHING)

    def mark_published(
        self, item_id: str, platform_results: dict[str, dict] | None = None
    ) -> ContentItem | None:
        item = self.get(item_id)
        if not item:
            return None
        item.status = ContentStatus.PUBLISHED.value
        item.published_at = datetime.now().isoformat()
        if platform_results:
            item.platforms.update(platform_results)
        item.updated_at = datetime.now().isoformat()
        self._save()
        return item

    def mark_failed(self, item_id: str, error: str = "") -> ContentItem | None:
        item = self.get(item_id)
        if not item:
            return None
        item.status = ContentStatus.FAILED.value
        item.notes = f"Failed: {error}"
        item.updated_at = datetime.now().isoformat()
        self._save()
        return item

    def archive(self, item_id: str) -> ContentItem | None:
        item = self.get(item_id)
        if not item:
            return None
        item.status = ContentStatus.ARCHIVED.value
        item.archived_at = datetime.now().isoformat()
        item.updated_at = datetime.now().isoformat()
        self._save()
        return item

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def list_by_status(self, status: str) -> list[ContentItem]:
        return [i for i in self._items if i.status == status]

    def list_by_campaign(self, campaign_id: str) -> list[ContentItem]:
        return [i for i in self._items if i.campaign_id == campaign_id]

    def list_by_tag(self, tag: str) -> list[ContentItem]:
        return [i for i in self._items if tag in i.tags]

    def list_scheduled(self) -> list[ContentItem]:
        return sorted(
            [i for i in self._items if i.status == ContentStatus.SCHEDULED.value],
            key=lambda x: x.scheduled_at,
        )

    def search(self, query: str) -> list[ContentItem]:
        q = query.lower()
        return [
            i for i in self._items
            if q in i.title.lower()
            or q in i.topic.lower()
            or q in i.caption.lower()
            or q in i.category.lower()
        ]

    def get_stats(self) -> dict:
        counts: dict[str, int] = {}
        for item in self._items:
            counts[item.status] = counts.get(item.status, 0) + 1
        return {
            "total": len(self._items),
            "by_status": counts,
        }

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self, status_filter: str = "", limit: int = 20) -> str:
        items = self._items
        if status_filter:
            items = [i for i in items if i.status == status_filter]

        lines = [
            "=" * 75,
            "  Content Management System",
            "=" * 75,
        ]

        stats = self.get_stats()
        parts = [f"{k}: {v}" for k, v in stats["by_status"].items()]
        lines.append(f"  Total: {stats['total']} | {' | '.join(parts)}")
        lines.append("")

        status_icons = {
            "draft": "[D]", "review": "[R]", "approved": "[A]",
            "scheduled": "[S]", "publishing": "[~]", "published": "[+]",
            "failed": "[-]", "archived": "[X]",
        }

        for item in items[-limit:]:
            icon = status_icons.get(item.status, "[ ]")
            platforms = ",".join(item.target_platforms[:3]) if item.target_platforms else "none"
            lines.append(
                f"  {icon} {item.id:<12} {item.content_type:<9} "
                f"{item.category:<14} [{platforms:<12}] "
                f"{item.title[:25] or item.topic[:25]}"
            )

        lines.append("=" * 75)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _transition(self, item_id: str, new_status: ContentStatus) -> ContentItem | None:
        item = self.get(item_id)
        if not item:
            return None
        item.status = new_status.value
        item.updated_at = datetime.now().isoformat()
        self._save()
        logger.info("cms.transition", id=item_id, status=new_status.value)
        return item

    def _load(self) -> None:
        if CMS_FILE.exists():
            try:
                data = json.loads(CMS_FILE.read_text())
                self._items = [ContentItem(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._items = []

    def _save(self) -> None:
        CMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(item) for item in self._items]
        CMS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
