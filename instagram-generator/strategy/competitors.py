"""Competitor tracking — monitor competitor social media accounts.

Features:
  - Track competitor account metrics over time
  - Compare posting frequency and engagement
  - Identify content gaps and opportunities
  - Manual data entry (API access requires competitor auth)
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

COMPETITORS_FILE = Path(settings.content_output_dir) / "competitors.json"


@dataclass
class CompetitorAccount:
    """A competitor account to track."""

    id: str = ""
    name: str = ""
    platform: str = "instagram"
    handle: str = ""
    url: str = ""

    # Metrics (manually updated)
    followers: int = 0
    posts_count: int = 0
    avg_likes: int = 0
    avg_comments: int = 0
    posting_frequency: str = ""  # e.g., "3/day", "5/week"
    top_content_types: list[str] = field(default_factory=list)
    top_categories: list[str] = field(default_factory=list)
    top_hashtags: list[str] = field(default_factory=list)

    notes: str = ""
    last_checked: str = ""
    history: list[dict] = field(default_factory=list)

    def record_snapshot(self) -> None:
        """Save current metrics as a historical snapshot."""
        self.history.append({
            "date": datetime.now().isoformat()[:10],
            "followers": self.followers,
            "posts_count": self.posts_count,
            "avg_likes": self.avg_likes,
            "avg_comments": self.avg_comments,
        })
        self.last_checked = datetime.now().isoformat()


class CompetitorTracker:
    """Track and analyze competitor accounts."""

    def __init__(self) -> None:
        self._competitors: list[CompetitorAccount] = []
        self._load()

    def add(self, **kwargs) -> CompetitorAccount:
        import uuid
        comp = CompetitorAccount(id=uuid.uuid4().hex[:8], **kwargs)
        self._competitors.append(comp)
        self._save()
        logger.info("competitor.added", name=comp.name, platform=comp.platform)
        return comp

    def get(self, comp_id: str) -> CompetitorAccount | None:
        for c in self._competitors:
            if c.id == comp_id:
                return c
        return None

    def update_metrics(
        self,
        comp_id: str,
        followers: int = 0,
        posts_count: int = 0,
        avg_likes: int = 0,
        avg_comments: int = 0,
    ) -> CompetitorAccount | None:
        comp = self.get(comp_id)
        if not comp:
            return None

        if followers:
            comp.followers = followers
        if posts_count:
            comp.posts_count = posts_count
        if avg_likes:
            comp.avg_likes = avg_likes
        if avg_comments:
            comp.avg_comments = avg_comments

        comp.record_snapshot()
        self._save()
        return comp

    def remove(self, comp_id: str) -> bool:
        comp = self.get(comp_id)
        if not comp:
            return False
        self._competitors.remove(comp)
        self._save()
        return True

    def get_all(self) -> list[CompetitorAccount]:
        return list(self._competitors)

    def compare(self) -> str:
        """Compare all tracked competitors."""
        lines = [
            "=" * 75,
            "  Competitor Comparison",
            "=" * 75,
        ]

        if not self._competitors:
            lines.append("  No competitors tracked yet.")
            lines.append("=" * 75)
            return "\n".join(lines)

        lines.append(
            f"  {'Name':<18} {'Platform':<10} {'Followers':<12} "
            f"{'Avg Likes':<11} {'Avg Comments':<13} {'Frequency'}"
        )
        lines.append("  " + "-" * 70)

        sorted_comps = sorted(self._competitors, key=lambda c: c.followers, reverse=True)
        for c in sorted_comps:
            lines.append(
                f"  {c.name:<18} {c.platform:<10} {c.followers:<12,} "
                f"{c.avg_likes:<11,} {c.avg_comments:<13,} {c.posting_frequency}"
            )

        # Insights
        if len(self._competitors) >= 2:
            all_hashtags: list[str] = []
            all_categories: list[str] = []
            for c in self._competitors:
                all_hashtags.extend(c.top_hashtags)
                all_categories.extend(c.top_categories)

            if all_hashtags:
                from collections import Counter
                common = Counter(all_hashtags).most_common(5)
                lines.append(f"\n  Common hashtags: {', '.join(f'#{h}' for h, _ in common)}")

            if all_categories:
                from collections import Counter
                common = Counter(all_categories).most_common(3)
                lines.append(f"  Popular categories: {', '.join(c for c, _ in common)}")

        lines.append("=" * 75)
        return "\n".join(lines)

    def display(self) -> str:
        return self.compare()

    def _load(self) -> None:
        if COMPETITORS_FILE.exists():
            try:
                data = json.loads(COMPETITORS_FILE.read_text())
                self._competitors = [CompetitorAccount(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._competitors = []

    def _save(self) -> None:
        COMPETITORS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(c) for c in self._competitors]
        COMPETITORS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
