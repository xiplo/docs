"""Follower funnel — track audience journey from discovery to advocacy.

Funnel stages:
  1. Awareness   — Impressions, reach (they saw your content)
  2. Interest    — Profile visits, follows (they checked you out)
  3. Engagement  — Likes, comments, shares (they interact)
  4. Conversion  — Saves, link clicks, DMs (they take action)
  5. Advocacy    — Shares, tags, UGC (they spread the word)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

FUNNEL_FILE = Path(settings.content_output_dir) / "funnel_data.json"


@dataclass
class FunnelSnapshot:
    """A point-in-time snapshot of funnel metrics."""

    date: str = ""
    platform: str = "all"

    # Stage 1: Awareness
    impressions: int = 0
    reach: int = 0

    # Stage 2: Interest
    profile_visits: int = 0
    new_followers: int = 0

    # Stage 3: Engagement
    total_likes: int = 0
    total_comments: int = 0
    total_shares: int = 0

    # Stage 4: Conversion
    total_saves: int = 0
    link_clicks: int = 0
    dms_received: int = 0

    # Stage 5: Advocacy
    mentions: int = 0
    user_tags: int = 0
    reposts: int = 0

    def __post_init__(self):
        if not self.date:
            self.date = datetime.now().isoformat()[:10]

    @property
    def awareness_to_interest(self) -> float:
        """Conversion rate: Awareness → Interest."""
        return (self.profile_visits / self.reach * 100) if self.reach else 0.0

    @property
    def interest_to_engagement(self) -> float:
        """Conversion rate: Interest → Engagement."""
        engagement = self.total_likes + self.total_comments + self.total_shares
        return (engagement / self.profile_visits * 100) if self.profile_visits else 0.0

    @property
    def engagement_to_conversion(self) -> float:
        """Conversion rate: Engagement → Conversion."""
        engagement = self.total_likes + self.total_comments + self.total_shares
        conversion = self.total_saves + self.link_clicks
        return (conversion / engagement * 100) if engagement else 0.0


class FollowerFunnel:
    """Track and analyze the follower acquisition funnel."""

    def __init__(self) -> None:
        self._snapshots: list[FunnelSnapshot] = []
        self._load()

    def record(self, **kwargs) -> FunnelSnapshot:
        snapshot = FunnelSnapshot(**kwargs)
        self._snapshots.append(snapshot)
        self._save()
        return snapshot

    def get_latest(self, platform: str = "all") -> FunnelSnapshot | None:
        filtered = [s for s in self._snapshots if s.platform == platform]
        return filtered[-1] if filtered else None

    def get_trend(self, platform: str = "all", days: int = 30) -> list[FunnelSnapshot]:
        filtered = [s for s in self._snapshots if s.platform == platform]
        return filtered[-days:]

    def display(self) -> str:
        lines = [
            "=" * 70,
            "  Follower Funnel",
            "=" * 70,
        ]

        latest = self.get_latest()
        if not latest:
            lines.append("  No funnel data yet. Record snapshots to see metrics.")
            lines.append("=" * 70)
            return "\n".join(lines)

        lines.append(f"  Date: {latest.date}  |  Platform: {latest.platform}")
        lines.append("")

        funnel_data = [
            ("Awareness", f"Impressions: {latest.impressions:,}  |  Reach: {latest.reach:,}"),
            ("Interest", f"Profile visits: {latest.profile_visits:,}  |  New followers: {latest.new_followers:,}"),
            ("Engagement", f"Likes: {latest.total_likes:,}  |  Comments: {latest.total_comments:,}  |  Shares: {latest.total_shares:,}"),
            ("Conversion", f"Saves: {latest.total_saves:,}  |  Link clicks: {latest.link_clicks:,}"),
            ("Advocacy", f"Mentions: {latest.mentions:,}  |  Tags: {latest.user_tags:,}  |  Reposts: {latest.reposts:,}"),
        ]

        for stage, metrics in funnel_data:
            lines.append(f"  {stage:<14} {metrics}")

        lines.append(f"\n  Conversion Rates:")
        lines.append(f"    Awareness → Interest:    {latest.awareness_to_interest:.1f}%")
        lines.append(f"    Interest → Engagement:   {latest.interest_to_engagement:.1f}%")
        lines.append(f"    Engagement → Conversion: {latest.engagement_to_conversion:.1f}%")

        lines.append("=" * 70)
        return "\n".join(lines)

    def _load(self) -> None:
        if FUNNEL_FILE.exists():
            try:
                data = json.loads(FUNNEL_FILE.read_text())
                self._snapshots = [FunnelSnapshot(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._snapshots = []

    def _save(self) -> None:
        FUNNEL_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(s) for s in self._snapshots]
        FUNNEL_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
