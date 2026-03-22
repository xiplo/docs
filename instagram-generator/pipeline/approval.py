"""Content approval workflow — review before publishing.

Modes:
  - auto:    Publish immediately if quality score passes (default)
  - review:  Save to review queue, wait for manual approval
  - preview: Generate content but don't publish (dry-run)

The review queue stores generated content with preview URLs.
Approved content is moved to the publish queue.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

REVIEW_FILE = Path(settings.content_output_dir) / "review_queue.json"


@dataclass
class ReviewItem:
    """Content awaiting manual approval."""

    id: str = ""
    topic: str = ""
    category: str = ""
    content_type: str = "reel"
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    voiceover_text: str = ""
    image_prompt: str = ""
    quality_scores: dict = field(default_factory=dict)
    preview_urls: list[str] = field(default_factory=list)
    local_paths: list[str] = field(default_factory=list)
    status: str = "pending"  # pending, approved, rejected, expired
    reviewer_notes: str = ""
    created_at: str = ""
    reviewed_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class ApprovalWorkflow:
    """Manages content review and approval before publishing."""

    def __init__(self) -> None:
        self._items: list[ReviewItem] = []
        self._load()

    def submit_for_review(
        self,
        request_id: str,
        topic: str,
        category: str,
        content_type: str,
        caption: str,
        hashtags: list[str],
        voiceover_text: str = "",
        image_prompt: str = "",
        quality_scores: dict = None,
        preview_urls: list[str] = None,
        local_paths: list[str] = None,
    ) -> ReviewItem:
        """Submit generated content for manual review."""
        item = ReviewItem(
            id=request_id,
            topic=topic,
            category=category,
            content_type=content_type,
            caption=caption,
            hashtags=hashtags,
            voiceover_text=voiceover_text,
            image_prompt=image_prompt,
            quality_scores=quality_scores or {},
            preview_urls=preview_urls or [],
            local_paths=local_paths or [],
        )
        self._items.append(item)
        self._save()
        logger.info("approval.submitted", id=request_id, topic=topic)
        return item

    def approve(self, item_id: str, notes: str = "") -> ReviewItem | None:
        """Approve a review item for publishing."""
        item = self._find(item_id)
        if not item or item.status != "pending":
            return None

        item.status = "approved"
        item.reviewer_notes = notes
        item.reviewed_at = datetime.now().isoformat()
        self._save()
        logger.info("approval.approved", id=item_id)
        return item

    def reject(self, item_id: str, reason: str = "") -> ReviewItem | None:
        """Reject a review item."""
        item = self._find(item_id)
        if not item or item.status != "pending":
            return None

        item.status = "rejected"
        item.reviewer_notes = reason
        item.reviewed_at = datetime.now().isoformat()
        self._save()
        logger.info("approval.rejected", id=item_id, reason=reason[:100])
        return item

    def get_pending(self) -> list[ReviewItem]:
        """Get all items awaiting review."""
        return [i for i in self._items if i.status == "pending"]

    def get_approved(self) -> list[ReviewItem]:
        """Get approved items ready for publishing."""
        return [i for i in self._items if i.status == "approved"]

    def display(self, status_filter: str = "") -> str:
        """Display review queue."""
        items = self._items
        if status_filter:
            items = [i for i in items if i.status == status_filter]

        lines = [
            "=" * 70,
            "  Content Review Queue",
            "=" * 70,
        ]

        status_icons = {
            "pending": "[?]",
            "approved": "[+]",
            "rejected": "[-]",
            "expired": "[x]",
        }

        counts = {}
        for item in self._items:
            counts[item.status] = counts.get(item.status, 0) + 1
        lines.append(f"  " + " | ".join(f"{k}: {v}" for k, v in counts.items()))
        lines.append("")

        for item in items[-20:]:
            icon = status_icons.get(item.status, "[ ]")
            avg_score = (
                sum(item.quality_scores.values()) / len(item.quality_scores)
                if item.quality_scores else 0
            )
            lines.append(
                f"  {icon} {item.id[:10]:<12} {item.content_type:<9} "
                f"{item.category:<14} Q:{avg_score:.1f}  "
                f"{item.topic[:25]}"
            )
            if item.reviewer_notes:
                lines.append(f"      Note: {item.reviewer_notes[:50]}")

        lines.append("=" * 70)
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _find(self, item_id: str) -> ReviewItem | None:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def _load(self) -> None:
        if REVIEW_FILE.exists():
            try:
                data = json.loads(REVIEW_FILE.read_text())
                self._items = [ReviewItem(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._items = []

    def _save(self) -> None:
        REVIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(item) for item in self._items]
        REVIEW_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
