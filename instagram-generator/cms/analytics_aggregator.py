"""Unified cross-platform analytics — aggregate performance across all platforms.

Collects and normalizes metrics from:
  - Instagram (impressions, reach, engagement)
  - Twitter/X (impressions, likes, retweets)
  - TikTok (views, likes, shares)
  - YouTube (views, likes, comments)
  - Facebook (reach, engagement, reactions)
  - Telegram (views, forwards)
  - LinkedIn (impressions, clicks, reactions)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

ANALYTICS_FILE = Path(settings.content_output_dir) / "cross_platform_analytics.json"


@dataclass
class PlatformMetrics:
    """Normalized metrics for a single platform."""

    platform: str = ""
    publish_id: str = ""
    impressions: int = 0
    reach: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    clicks: int = 0
    views: int = 0
    collected_at: str = ""

    @property
    def engagement_rate(self) -> float:
        total_engagement = self.likes + self.comments + self.shares + self.saves
        if self.impressions > 0:
            return total_engagement / self.impressions * 100
        return 0.0


@dataclass
class ContentAnalytics:
    """Analytics for a single content item across all platforms."""

    content_id: str = ""
    title: str = ""
    content_type: str = ""
    category: str = ""
    platform_metrics: list[dict] = field(default_factory=list)
    created_at: str = ""

    @property
    def total_impressions(self) -> int:
        return sum(m.get("impressions", 0) for m in self.platform_metrics)

    @property
    def total_engagement(self) -> int:
        return sum(
            m.get("likes", 0) + m.get("comments", 0) + m.get("shares", 0) + m.get("saves", 0)
            for m in self.platform_metrics
        )

    @property
    def best_platform(self) -> str:
        if not self.platform_metrics:
            return ""
        best = max(self.platform_metrics, key=lambda m: m.get("impressions", 0))
        return best.get("platform", "")


class AnalyticsAggregator:
    """Collect and analyze cross-platform performance."""

    def __init__(self) -> None:
        self._data: list[ContentAnalytics] = []
        self._load()

    def record(
        self,
        content_id: str,
        title: str,
        content_type: str,
        category: str,
        platform_metrics: list[PlatformMetrics],
    ) -> ContentAnalytics:
        """Record analytics for a content item."""
        entry = ContentAnalytics(
            content_id=content_id,
            title=title,
            content_type=content_type,
            category=category,
            platform_metrics=[asdict(m) for m in platform_metrics],
            created_at=datetime.now().isoformat(),
        )
        self._data.append(entry)
        self._save()
        return entry

    def get_by_content(self, content_id: str) -> ContentAnalytics | None:
        for entry in self._data:
            if entry.content_id == content_id:
                return entry
        return None

    def get_platform_summary(self) -> dict[str, dict]:
        """Aggregate metrics per platform."""
        summary: dict[str, dict] = {}

        for entry in self._data:
            for pm in entry.platform_metrics:
                p = pm.get("platform", "unknown")
                if p not in summary:
                    summary[p] = {
                        "posts": 0, "impressions": 0, "engagement": 0,
                        "likes": 0, "comments": 0, "shares": 0,
                    }
                summary[p]["posts"] += 1
                summary[p]["impressions"] += pm.get("impressions", 0)
                summary[p]["likes"] += pm.get("likes", 0)
                summary[p]["comments"] += pm.get("comments", 0)
                summary[p]["shares"] += pm.get("shares", 0)
                summary[p]["engagement"] += (
                    pm.get("likes", 0) + pm.get("comments", 0) +
                    pm.get("shares", 0) + pm.get("saves", 0)
                )

        return summary

    def get_category_performance(self) -> dict[str, dict]:
        """Performance broken down by category."""
        cats: dict[str, dict] = {}

        for entry in self._data:
            cat = entry.category or "uncategorized"
            if cat not in cats:
                cats[cat] = {"posts": 0, "total_impressions": 0, "total_engagement": 0}
            cats[cat]["posts"] += 1
            cats[cat]["total_impressions"] += entry.total_impressions
            cats[cat]["total_engagement"] += entry.total_engagement

        return cats

    def get_best_performing(self, limit: int = 5) -> list[ContentAnalytics]:
        """Get top performing content by total engagement."""
        return sorted(
            self._data,
            key=lambda x: x.total_engagement,
            reverse=True,
        )[:limit]

    def generate_report(self) -> str:
        """Generate a cross-platform analytics report."""
        lines = [
            "=" * 70,
            "  Cross-Platform Analytics Report",
            f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 70,
        ]

        # Platform summary
        summary = self.get_platform_summary()
        if summary:
            lines.append("\n  PLATFORM PERFORMANCE")
            lines.append(f"  {'Platform':<12} {'Posts':<7} {'Impressions':<14} {'Engagement':<12} {'Likes':<8}")
            lines.append("  " + "-" * 55)
            for p, s in sorted(summary.items(), key=lambda x: x[1]["impressions"], reverse=True):
                lines.append(
                    f"  {p:<12} {s['posts']:<7} {s['impressions']:<14,} "
                    f"{s['engagement']:<12,} {s['likes']:<8,}"
                )
        else:
            lines.append("\n  No analytics data yet.")

        # Category performance
        cats = self.get_category_performance()
        if cats:
            lines.append(f"\n  CATEGORY PERFORMANCE")
            for cat, data in sorted(cats.items(), key=lambda x: x[1]["total_engagement"], reverse=True):
                avg_eng = data["total_engagement"] / data["posts"] if data["posts"] else 0
                lines.append(
                    f"  {cat:<16} {data['posts']} posts  "
                    f"reach={data['total_impressions']:,}  "
                    f"engagement={data['total_engagement']:,}  "
                    f"avg={avg_eng:,.0f}"
                )

        # Top content
        top = self.get_best_performing(5)
        if top:
            lines.append(f"\n  TOP PERFORMERS")
            for entry in top:
                lines.append(
                    f"  {entry.content_id:<12} {entry.content_type:<8} "
                    f"reach={entry.total_impressions:,}  "
                    f"eng={entry.total_engagement:,}  "
                    f"best={entry.best_platform}"
                )

        lines.append("=" * 70)
        return "\n".join(lines)

    def _load(self) -> None:
        if ANALYTICS_FILE.exists():
            try:
                data = json.loads(ANALYTICS_FILE.read_text())
                self._data = [ContentAnalytics(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._data = []

    def _save(self) -> None:
        ANALYTICS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(entry) for entry in self._data]
        ANALYTICS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
