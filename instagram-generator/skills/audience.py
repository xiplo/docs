"""Audience skills — targeting and personalization intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass
class AudienceSegment:
    name: str
    age_range: tuple[int, int]
    interests: list[str]
    peak_hours: list[int]  # Hours in Tashkent time
    preferred_content: list[str]
    tone: str
    language_mix: str  # "uzbek_only", "uzbek_russian", "mixed"


# Uzbek Instagram audience segments
SEGMENTS = {
    "young_professionals": AudienceSegment(
        name="Yosh mutaxassislar",
        age_range=(22, 35),
        interests=["career", "tech", "education", "self-improvement"],
        peak_hours=[8, 9, 12, 13, 18, 19, 20, 21],
        preferred_content=["reel", "carousel"],
        tone="professional yet approachable",
        language_mix="mixed",
    ),
    "students": AudienceSegment(
        name="Talabalar",
        age_range=(16, 24),
        interests=["education", "tech", "humor", "lifestyle", "fashion"],
        peak_hours=[10, 11, 14, 15, 20, 21, 22, 23],
        preferred_content=["reel", "story"],
        tone="casual, friendly, trendy",
        language_mix="mixed",
    ),
    "homemakers": AudienceSegment(
        name="Uy bekalari",
        age_range=(25, 45),
        interests=["recipe", "lifestyle", "fashion", "family"],
        peak_hours=[9, 10, 11, 14, 15, 16],
        preferred_content=["reel", "carousel", "image"],
        tone="warm, helpful, relatable",
        language_mix="uzbek_only",
    ),
    "entrepreneurs": AudienceSegment(
        name="Tadbirkorlar",
        age_range=(25, 50),
        interests=["business", "motivational", "product", "tech"],
        peak_hours=[7, 8, 12, 13, 18, 21, 22],
        preferred_content=["reel", "carousel"],
        tone="authoritative, inspiring, direct",
        language_mix="uzbek_russian",
    ),
    "travelers": AudienceSegment(
        name="Sayohatchilar",
        age_range=(20, 40),
        interests=["travel", "lifestyle", "photography", "culture"],
        peak_hours=[9, 10, 18, 19, 20, 21],
        preferred_content=["reel", "carousel", "image"],
        tone="adventurous, visual-first, storytelling",
        language_mix="mixed",
    ),
}


class AudienceSkills:
    """Skills for audience targeting and content optimization."""

    @staticmethod
    def get_best_posting_time(
        segment: str,
        timezone: str = "Asia/Tashkent",
    ) -> list[int]:
        """Get optimal posting hours for a segment."""
        seg = SEGMENTS.get(segment)
        if seg:
            return seg.peak_hours
        # Default peaks
        return [9, 13, 18]

    @staticmethod
    def get_segment_for_category(category: str) -> list[AudienceSegment]:
        """Find audience segments that match a content category."""
        matches = []
        for seg in SEGMENTS.values():
            if category in seg.interests:
                matches.append(seg)
        return matches or list(SEGMENTS.values())[:2]

    @staticmethod
    def get_optimal_content_type(segment: str) -> str:
        """Get the preferred content type for a segment."""
        seg = SEGMENTS.get(segment)
        if seg and seg.preferred_content:
            return seg.preferred_content[0]
        return "reel"

    @staticmethod
    def is_peak_hour(
        segment: str,
        timezone: str = "Asia/Tashkent",
    ) -> bool:
        """Check if current time is a peak hour for the segment."""
        seg = SEGMENTS.get(segment)
        if not seg:
            return False
        now = datetime.now(ZoneInfo(timezone))
        return now.hour in seg.peak_hours

    @staticmethod
    def get_tone(segment: str) -> str:
        """Get the appropriate tone for a segment."""
        seg = SEGMENTS.get(segment)
        return seg.tone if seg else "friendly and approachable"

    @staticmethod
    def get_language_strategy(segment: str) -> dict[str, str]:
        """Get language mixing strategy for captions and voiceover."""
        seg = SEGMENTS.get(segment)
        if not seg:
            return {"caption": "uzbek", "voiceover": "uzbek", "hashtags": "mixed"}

        strategies = {
            "uzbek_only": {
                "caption": "uzbek",
                "voiceover": "uzbek",
                "hashtags": "uzbek",
            },
            "uzbek_russian": {
                "caption": "uzbek with russian terms for technical concepts",
                "voiceover": "uzbek",
                "hashtags": "mixed uzbek/russian",
            },
            "mixed": {
                "caption": "uzbek primary, english for trends/tech terms",
                "voiceover": "uzbek",
                "hashtags": "mixed uzbek/english",
            },
        }
        return strategies.get(seg.language_mix, strategies["mixed"])
