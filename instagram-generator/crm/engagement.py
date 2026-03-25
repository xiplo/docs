"""Engagement tracking — monitor and analyze audience interactions.

Tracks per-post and aggregate engagement:
  - Likes, comments, shares, saves per post
  - Engagement rate over time
  - Top engaged users (potential advocates)
  - Content-audience fit scoring
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

ENGAGEMENT_FILE = Path(settings.content_output_dir) / "engagement_data.json"


@dataclass
class PostEngagement:
    """Engagement data for a single post."""

    post_id: str = ""
    content_id: str = ""
    platform: str = ""
    content_type: str = ""
    category: str = ""

    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    impressions: int = 0
    reach: int = 0
    profile_visits: int = 0
    follows: int = 0

    posted_at: str = ""
    recorded_at: str = ""

    @property
    def engagement_rate(self) -> float:
        total = self.likes + self.comments + self.shares + self.saves
        return (total / self.impressions * 100) if self.impressions else 0.0

    @property
    def total_interactions(self) -> int:
        return self.likes + self.comments + self.shares + self.saves

    def __post_init__(self):
        if not self.recorded_at:
            self.recorded_at = datetime.now().isoformat()


class EngagementTracker:
    """Track and analyze content engagement."""

    def __init__(self) -> None:
        self._records: list[PostEngagement] = []
        self._load()

    def record(self, **kwargs) -> PostEngagement:
        entry = PostEngagement(**kwargs)
        self._records.append(entry)
        self._save()
        return entry

    def get_by_content(self, content_id: str) -> list[PostEngagement]:
        return [r for r in self._records if r.content_id == content_id]

    def get_by_platform(self, platform: str) -> list[PostEngagement]:
        return [r for r in self._records if r.platform == platform]

    def avg_engagement_rate(self, platform: str = "") -> float:
        records = self.get_by_platform(platform) if platform else self._records
        rates = [r.engagement_rate for r in records if r.impressions > 0]
        return sum(rates) / len(rates) if rates else 0.0

    def top_posts(self, limit: int = 10) -> list[PostEngagement]:
        return sorted(
            self._records,
            key=lambda r: r.total_interactions,
            reverse=True,
        )[:limit]

    def category_performance(self) -> dict[str, dict]:
        cats: dict[str, dict] = defaultdict(
            lambda: {"posts": 0, "total_likes": 0, "total_comments": 0, "total_shares": 0, "total_impressions": 0}
        )
        for r in self._records:
            c = cats[r.category or "uncategorized"]
            c["posts"] += 1
            c["total_likes"] += r.likes
            c["total_comments"] += r.comments
            c["total_shares"] += r.shares
            c["total_impressions"] += r.impressions
        return dict(cats)

    def platform_comparison(self) -> dict[str, dict]:
        platforms: dict[str, dict] = defaultdict(
            lambda: {"posts": 0, "total_engagement": 0, "total_impressions": 0, "avg_rate": 0.0}
        )
        for r in self._records:
            p = platforms[r.platform]
            p["posts"] += 1
            p["total_engagement"] += r.total_interactions
            p["total_impressions"] += r.impressions
        for p, data in platforms.items():
            if data["total_impressions"]:
                data["avg_rate"] = round(data["total_engagement"] / data["total_impressions"] * 100, 2)
        return dict(platforms)

    def display(self) -> str:
        lines = [
            "=" * 70,
            "  Engagement Tracker",
            "=" * 70,
        ]

        if not self._records:
            lines.append("  No engagement data yet.")
            lines.append("=" * 70)
            return "\n".join(lines)

        lines.append(f"  Total records: {len(self._records)}")
        lines.append(f"  Overall avg engagement rate: {self.avg_engagement_rate():.2f}%")

        # Platform comparison
        platforms = self.platform_comparison()
        if platforms:
            lines.append("\n  Platform Performance:")
            for p, data in sorted(platforms.items(), key=lambda x: x[1]["total_engagement"], reverse=True):
                lines.append(
                    f"    {p:<14} {data['posts']} posts  "
                    f"eng={data['total_engagement']:,}  "
                    f"rate={data['avg_rate']:.1f}%"
                )

        # Top posts
        top = self.top_posts(5)
        if top:
            lines.append("\n  Top Posts:")
            for r in top:
                lines.append(
                    f"    {r.post_id[:12]:<14} {r.platform:<10} "
                    f"L={r.likes} C={r.comments} S={r.shares} "
                    f"rate={r.engagement_rate:.1f}%"
                )

        lines.append("=" * 70)
        return "\n".join(lines)

    def _load(self) -> None:
        if ENGAGEMENT_FILE.exists():
            try:
                data = json.loads(ENGAGEMENT_FILE.read_text())
                self._records = [PostEngagement(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._records = []

    def _save(self) -> None:
        ENGAGEMENT_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(r) for r in self._records]
        ENGAGEMENT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
