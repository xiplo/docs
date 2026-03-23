"""Hashtag research — find optimal hashtags for content.

Features:
  - Category-based hashtag sets (curated for Uzbek audience)
  - Mix of reach tiers: broad (>1M), mid (100K-1M), niche (<100K)
  - Related hashtag suggestions
  - Banned hashtag detection (shadowban risk)
  - Optimal count recommendation (8-15 per post)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# Hashtags that can cause shadowban or reduced reach
BANNED_HASHTAGS = frozenset({
    "follow4follow", "f4f", "like4like", "l4l", "followback",
    "instalike", "likeforlike", "followforfollow", "instadaily",
    "tagsforlikes", "followme", "igers", "instagood",
})

# Curated hashtag pools by category — mix of UZ, RU, EN
HASHTAG_POOLS: dict[str, dict[str, list[str]]] = {
    "motivational": {
        "broad": ["motivation", "success", "mindset", "hustle", "grind"],
        "mid": [
            "uzbekmotivation", "motivatsiya", "muvaffaqiyat",
            "biznes", "tadbirkorlik", "startupuz",
        ],
        "niche": [
            "uzbekbusiness", "toshkentlife", "uzstartup",
            "uzbekentrepreneur", "ishonch", "mehnat",
        ],
    },
    "recipe": {
        "broad": ["foodie", "cooking", "homemade", "yummy", "delicious"],
        "mid": [
            "uzbekfood", "ozbektaomi", "palov", "taom",
            "oshpaz", "uzbekcuisine",
        ],
        "niche": [
            "uzbekrecipe", "somsa", "lagman", "shashlikuz",
            "nonuz", "toshkenttaom", "milliytalim",
        ],
    },
    "travel": {
        "broad": ["travel", "explore", "wanderlust", "travelphotography"],
        "mid": [
            "uzbekistan", "centralasia", "silkroad", "tashkent",
            "samarkand", "bukhara", "khiva",
        ],
        "niche": [
            "visituzbekistan", "traveluzbekistan", "uzbektravel",
            "registon", "ichanqala", "chorminor",
        ],
    },
    "lifestyle": {
        "broad": ["lifestyle", "dailylife", "morningroutine", "aesthetic"],
        "mid": [
            "uzbeklifestyle", "tashkentlife", "hayot", "kundalik",
            "oilaviy", "turmush",
        ],
        "niche": [
            "uzbekgirl", "uzbekboy", "toshkentlik",
            "uzbekstyle", "hayotiy", "kunliklayon",
        ],
    },
    "education": {
        "broad": ["education", "learning", "knowledge", "study"],
        "mid": [
            "uzbekeducation", "talim", "ilm", "kitob",
            "oqish", "bilim",
        ],
        "niche": [
            "uztalim", "ozbektili", "darslik",
            "matematika", "tarix", "fanlar",
        ],
    },
    "fitness": {
        "broad": ["fitness", "gym", "workout", "healthy", "fitlife"],
        "mid": [
            "fitnesuz", "sportuzbek", "salomatlik",
            "mashqlar", "trenajorzal",
        ],
        "niche": [
            "uzbekfitness", "tashkentgym", "sportuzb",
            "soglomhayot", "ochiqhavo",
        ],
    },
}


@dataclass
class HashtagSet:
    """A curated set of hashtags with metadata."""

    tags: list[str] = field(default_factory=list)
    category: str = ""
    broad_count: int = 0
    mid_count: int = 0
    niche_count: int = 0
    banned_removed: list[str] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.tags)

    def as_string(self) -> str:
        return " ".join(f"#{t}" for t in self.tags)


class HashtagResearch:
    """Research and suggest optimal hashtags."""

    OPTIMAL_MIN = 8
    OPTIMAL_MAX = 15

    # Ratio: ~30% broad, ~40% mid, ~30% niche
    TIER_RATIOS = {"broad": 0.30, "mid": 0.40, "niche": 0.30}

    @classmethod
    def suggest(
        cls,
        category: str,
        count: int = 12,
        extra_tags: list[str] | None = None,
    ) -> HashtagSet:
        """Suggest optimal hashtags for a category."""
        pool = HASHTAG_POOLS.get(category, HASHTAG_POOLS.get("motivational", {}))
        count = max(cls.OPTIMAL_MIN, min(count, cls.OPTIMAL_MAX))

        broad_n = max(2, int(count * cls.TIER_RATIOS["broad"]))
        niche_n = max(2, int(count * cls.TIER_RATIOS["niche"]))
        mid_n = count - broad_n - niche_n

        broad = random.sample(pool.get("broad", []), min(broad_n, len(pool.get("broad", []))))
        mid = random.sample(pool.get("mid", []), min(mid_n, len(pool.get("mid", []))))
        niche = random.sample(pool.get("niche", []), min(niche_n, len(pool.get("niche", []))))

        tags = broad + mid + niche

        # Add extra tags
        if extra_tags:
            for tag in extra_tags:
                clean = tag.strip("#").lower()
                if clean and clean not in tags:
                    tags.append(clean)

        # Remove banned hashtags
        banned_found = [t for t in tags if t.lower() in BANNED_HASHTAGS]
        tags = [t for t in tags if t.lower() not in BANNED_HASHTAGS]

        result = HashtagSet(
            tags=tags[:cls.OPTIMAL_MAX],
            category=category,
            broad_count=len(broad),
            mid_count=len(mid),
            niche_count=len(niche),
            banned_removed=banned_found,
        )

        if banned_found:
            logger.warning("hashtag.banned_removed", removed=banned_found)

        return result

    @classmethod
    def check_banned(cls, tags: list[str]) -> list[str]:
        """Check a list of tags for banned/risky hashtags."""
        return [t for t in tags if t.strip("#").lower() in BANNED_HASHTAGS]

    @classmethod
    def get_related(cls, category: str) -> list[str]:
        """Get all available hashtags for a category."""
        pool = HASHTAG_POOLS.get(category, {})
        tags = []
        for tier_tags in pool.values():
            tags.extend(tier_tags)
        return tags

    @classmethod
    def display(cls, category: str = "") -> str:
        """Display available hashtag pools."""
        lines = [
            "=" * 60,
            "  Hashtag Research",
            "=" * 60,
        ]

        categories = [category] if category else list(HASHTAG_POOLS.keys())

        for cat in categories:
            pool = HASHTAG_POOLS.get(cat, {})
            if not pool:
                continue

            lines.append(f"\n  {cat.upper()}")
            for tier, tags in pool.items():
                tag_str = ", ".join(f"#{t}" for t in tags)
                lines.append(f"    {tier:<6} ({len(tags)}): {tag_str}")

            suggestion = cls.suggest(cat)
            lines.append(f"    Suggested ({suggestion.total}): {suggestion.as_string()}")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
