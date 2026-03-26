"""Audience management — segment and track audience groups.

Segments:
  - Demographics (age, location, language)
  - Behavior (engagement level, content preferences)
  - Platform affinity (which platforms they're most active on)
  - Lifecycle stage (new follower, engaged, advocate, churned)
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

AUDIENCE_FILE = Path(settings.content_output_dir) / "audience_segments.json"


@dataclass
class AudienceSegment:
    """A defined audience segment."""

    id: str = ""
    name: str = ""
    description: str = ""

    # Demographics
    age_range: str = "18-35"
    locations: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)

    # Behavior
    preferred_content: list[str] = field(default_factory=list)
    preferred_categories: list[str] = field(default_factory=list)
    engagement_level: str = "medium"  # low, medium, high, super
    active_platforms: list[str] = field(default_factory=list)

    # Lifecycle
    stage: str = "active"  # new, active, engaged, advocate, at_risk, churned
    size_estimate: int = 0

    # Targeting
    best_posting_times: list[str] = field(default_factory=list)
    tone_preference: str = "casual"  # casual, professional, inspirational, humorous
    hashtag_affinity: list[str] = field(default_factory=list)

    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# Pre-built segments for Uzbek market (2026 DataReportal data)
# Uzbekistan: 33.1M internet users (89%), 14.1M social media identities
# Telegram 18M, Facebook 15.9M, Instagram 15.3M, TikTok 2.59M (18+)
# Median age 27, 67-68% male skew across platforms
DEFAULT_SEGMENTS = [
    AudienceSegment(
        id="uz_youth",
        name="Uzbek Youth (18-24)",
        description="5.3M on Instagram, 5.2M on Facebook — largest demographic, digital-native, Tashkent/Samarkand",
        age_range="18-24",
        locations=["Tashkent", "Samarkand", "Bukhara", "Namangan"],
        languages=["uz", "ru"],
        preferred_content=["reel", "story"],
        preferred_categories=["motivational", "lifestyle", "education", "humor"],
        engagement_level="high",
        active_platforms=["instagram", "tiktok", "telegram", "youtube"],
        stage="active",
        size_estimate=5300000,
        best_posting_times=["10:00", "19:00", "22:00"],
        tone_preference="casual",
    ),
    AudienceSegment(
        id="uz_professionals",
        name="Uzbek Professionals (25-34)",
        description="Career-focused, bilingual uz/ru/en, Tashkent-centric",
        age_range="25-34",
        locations=["Tashkent"],
        languages=["uz", "ru", "en"],
        preferred_content=["carousel", "image"],
        preferred_categories=["motivational", "education", "lifestyle"],
        engagement_level="medium",
        active_platforms=["instagram", "linkedin", "telegram", "facebook"],
        stage="active",
        size_estimate=3800000,
        best_posting_times=["07:30", "12:00", "18:00"],
        tone_preference="professional",
    ),
    AudienceSegment(
        id="uz_foodies",
        name="Uzbek Foodies (25-45)",
        description="Home cooks, traditional cuisine lovers, cross-platform",
        age_range="25-45",
        locations=["Tashkent", "Fergana", "Bukhara", "Samarkand"],
        languages=["uz", "ru"],
        preferred_content=["reel", "carousel"],
        preferred_categories=["recipe"],
        engagement_level="high",
        active_platforms=["instagram", "facebook", "tiktok", "youtube", "telegram"],
        stage="engaged",
        size_estimate=2500000,
        best_posting_times=["09:00", "12:00", "18:00"],
        tone_preference="casual",
    ),
    AudienceSegment(
        id="uz_telegram",
        name="Telegram-First Audience",
        description="18M Telegram users — dominant platform in Uzbekistan, news and community",
        age_range="18-45",
        locations=["Tashkent", "Samarkand", "Bukhara", "Namangan", "Fergana"],
        languages=["uz", "ru"],
        preferred_content=["image", "video"],
        preferred_categories=["motivational", "education", "recipe", "lifestyle"],
        engagement_level="high",
        active_platforms=["telegram"],
        stage="active",
        size_estimate=18000000,
        best_posting_times=["08:00", "12:00", "18:00", "21:00"],
        tone_preference="casual",
    ),
    AudienceSegment(
        id="international",
        name="International Travelers",
        description="English-speaking travelers, Silk Road interest, high-value",
        age_range="25-55",
        locations=["USA", "Europe", "Korea", "Japan", "Turkey"],
        languages=["en"],
        preferred_content=["reel", "image"],
        preferred_categories=["travel"],
        engagement_level="medium",
        active_platforms=["instagram", "youtube", "pinterest", "tiktok", "threads"],
        stage="new",
        size_estimate=500000,
        best_posting_times=["15:00", "20:00"],
        tone_preference="inspirational",
    ),
]


class AudienceManager:
    """Manage audience segments for targeted content."""

    def __init__(self) -> None:
        self._segments: list[AudienceSegment] = []
        self._load()
        if not self._segments:
            self._segments = list(DEFAULT_SEGMENTS)
            self._save()

    def get(self, segment_id: str) -> AudienceSegment | None:
        for s in self._segments:
            if s.id == segment_id:
                return s
        return None

    def create(self, **kwargs) -> AudienceSegment:
        segment = AudienceSegment(**kwargs)
        self._segments.append(segment)
        self._save()
        return segment

    def update(self, segment_id: str, **kwargs) -> AudienceSegment | None:
        segment = self.get(segment_id)
        if not segment:
            return None
        for key, val in kwargs.items():
            if hasattr(segment, key):
                setattr(segment, key, val)
        segment.updated_at = datetime.now().isoformat()
        self._save()
        return segment

    def get_all(self) -> list[AudienceSegment]:
        return list(self._segments)

    def get_for_content(self, category: str, content_type: str) -> list[AudienceSegment]:
        """Find audience segments that match a content type + category."""
        return [
            s for s in self._segments
            if category in s.preferred_categories or content_type in s.preferred_content
        ]

    def get_platforms_for_segment(self, segment_id: str) -> list[str]:
        """Get recommended platforms for a segment."""
        segment = self.get(segment_id)
        return segment.active_platforms if segment else ["instagram"]

    def display(self) -> str:
        lines = [
            "=" * 75,
            "  Audience Segments",
            "=" * 75,
        ]

        total = sum(s.size_estimate for s in self._segments)
        lines.append(f"  {len(self._segments)} segments | Est. total reach: {total:,}")
        lines.append("")

        for s in self._segments:
            platforms = ", ".join(s.active_platforms[:4])
            cats = ", ".join(s.preferred_categories[:3])
            lines.append(
                f"  [{s.stage[:3].upper()}] {s.id:<16} {s.name:<22} "
                f"{s.size_estimate:>8,}  {s.age_range}"
            )
            lines.append(f"          Platforms: {platforms}  |  Content: {cats}")

        lines.append("=" * 75)
        return "\n".join(lines)

    def _load(self) -> None:
        if AUDIENCE_FILE.exists():
            try:
                data = json.loads(AUDIENCE_FILE.read_text())
                self._segments = [AudienceSegment(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._segments = []

    def _save(self) -> None:
        AUDIENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(s) for s in self._segments]
        AUDIENCE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
