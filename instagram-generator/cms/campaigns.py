"""Campaign management — group content into marketing campaigns.

Features:
  - Name, date range, target platforms, goals
  - Track content items belonging to campaign
  - Campaign-level analytics (published/failed/pending counts)
  - Budget tracking (optional)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

CAMPAIGNS_FILE = Path(settings.content_output_dir) / "campaigns.json"


@dataclass
class Campaign:
    """A content campaign."""

    id: str = ""
    name: str = ""
    description: str = ""
    status: str = "active"  # active, paused, completed, archived

    # Targeting
    target_platforms: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Schedule
    start_date: str = ""
    end_date: str = ""

    # Goals
    goals: dict = field(default_factory=dict)  # {metric: target_value}

    # Tracking
    content_ids: list[str] = field(default_factory=list)
    published_count: int = 0
    failed_count: int = 0
    total_reach: int = 0
    total_engagement: int = 0

    # Metadata
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:10]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    @property
    def content_count(self) -> int:
        return len(self.content_ids)

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False
        now = datetime.now().isoformat()
        if self.end_date and now > self.end_date:
            return False
        return True


class CampaignManager:
    """Manage content campaigns."""

    def __init__(self) -> None:
        self._campaigns: list[Campaign] = []
        self._load()

    def create(self, **kwargs) -> Campaign:
        campaign = Campaign(**kwargs)
        self._campaigns.append(campaign)
        self._save()
        logger.info("campaign.created", id=campaign.id, name=campaign.name)
        return campaign

    def get(self, campaign_id: str) -> Campaign | None:
        for c in self._campaigns:
            if c.id == campaign_id:
                return c
        return None

    def get_by_name(self, name: str) -> Campaign | None:
        for c in self._campaigns:
            if c.name.lower() == name.lower():
                return c
        return None

    def update(self, campaign_id: str, **kwargs) -> Campaign | None:
        campaign = self.get(campaign_id)
        if not campaign:
            return None
        for key, val in kwargs.items():
            if hasattr(campaign, key):
                setattr(campaign, key, val)
        campaign.updated_at = datetime.now().isoformat()
        self._save()
        return campaign

    def add_content(self, campaign_id: str, content_id: str) -> bool:
        campaign = self.get(campaign_id)
        if not campaign:
            return False
        if content_id not in campaign.content_ids:
            campaign.content_ids.append(content_id)
            campaign.updated_at = datetime.now().isoformat()
            self._save()
        return True

    def record_publish(self, campaign_id: str, success: bool = True) -> None:
        campaign = self.get(campaign_id)
        if campaign:
            if success:
                campaign.published_count += 1
            else:
                campaign.failed_count += 1
            campaign.updated_at = datetime.now().isoformat()
            self._save()

    def complete(self, campaign_id: str) -> Campaign | None:
        return self.update(campaign_id, status="completed")

    def pause(self, campaign_id: str) -> Campaign | None:
        return self.update(campaign_id, status="paused")

    def resume(self, campaign_id: str) -> Campaign | None:
        return self.update(campaign_id, status="active")

    def get_active(self) -> list[Campaign]:
        return [c for c in self._campaigns if c.is_active]

    def get_all(self) -> list[Campaign]:
        return list(self._campaigns)

    def display(self) -> str:
        lines = [
            "=" * 70,
            "  Campaign Manager",
            "=" * 70,
        ]

        active = [c for c in self._campaigns if c.status == "active"]
        completed = [c for c in self._campaigns if c.status == "completed"]
        lines.append(f"  Active: {len(active)} | Completed: {len(completed)} | Total: {len(self._campaigns)}")
        lines.append("")

        status_icons = {"active": "[>]", "paused": "[|]", "completed": "[+]", "archived": "[X]"}

        for c in self._campaigns:
            icon = status_icons.get(c.status, "[ ]")
            platforms = ",".join(c.target_platforms[:3]) or "all"
            lines.append(
                f"  {icon} {c.id:<10} {c.name:<20} [{platforms:<12}] "
                f"content={c.content_count:<3} pub={c.published_count}"
            )
            if c.goals:
                goal_str = ", ".join(f"{k}={v}" for k, v in c.goals.items())
                lines.append(f"      Goals: {goal_str}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def _load(self) -> None:
        if CAMPAIGNS_FILE.exists():
            try:
                data = json.loads(CAMPAIGNS_FILE.read_text())
                self._campaigns = [Campaign(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._campaigns = []

    def _save(self) -> None:
        CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(c) for c in self._campaigns]
        CAMPAIGNS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
