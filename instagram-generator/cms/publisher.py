"""Publishing router — rules-based multi-platform content dispatch.

Rules determine which content goes to which platforms:
  - By content type (reels → IG + TikTok + YouTube)
  - By category (recipes → IG + Facebook + Telegram)
  - By campaign (all campaign content → specified platforms)
  - By schedule (different platforms at different times)

The router combines CMS, cross-poster, and queue for full automation.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

RULES_FILE = Path(settings.content_output_dir) / "publish_rules.json"


@dataclass
class PublishRule:
    """A rule that maps content to platforms."""

    id: str = ""
    name: str = ""
    enabled: bool = True

    # Conditions (all must match if set)
    content_type: str = ""  # reel, image, carousel, story
    category: str = ""
    campaign_id: str = ""
    tags: list[str] = field(default_factory=list)

    # Actions
    target_platforms: list[str] = field(default_factory=list)
    priority: int = 5
    delay_minutes: int = 0  # Stagger posting across platforms

    def matches(self, content: dict) -> bool:
        """Check if content matches this rule's conditions."""
        if self.content_type and content.get("content_type") != self.content_type:
            return False
        if self.category and content.get("category") != self.category:
            return False
        if self.campaign_id and content.get("campaign_id") != self.campaign_id:
            return False
        if self.tags:
            content_tags = set(content.get("tags", []))
            if not set(self.tags).intersection(content_tags):
                return False
        return True


# Default rules
DEFAULT_RULES: list[PublishRule] = [
    PublishRule(
        id="reels_multi",
        name="Reels → IG + TikTok + YouTube + Facebook",
        content_type="reel",
        target_platforms=["instagram", "tiktok", "youtube", "facebook"],
        priority=8,
    ),
    PublishRule(
        id="images_multi",
        name="Images → IG + Facebook + Telegram + LinkedIn",
        content_type="image",
        target_platforms=["instagram", "facebook", "telegram", "linkedin"],
        priority=6,
    ),
    PublishRule(
        id="carousel_multi",
        name="Carousels → IG + Facebook + Telegram + TikTok",
        content_type="carousel",
        target_platforms=["instagram", "facebook", "telegram", "tiktok"],
        priority=6,
    ),
    PublishRule(
        id="recipes_social",
        name="Recipes → IG + Facebook + Telegram",
        category="recipe",
        target_platforms=["instagram", "facebook", "telegram"],
        priority=7,
    ),
    PublishRule(
        id="motivational_everywhere",
        name="Motivational → All platforms",
        category="motivational",
        target_platforms=["instagram", "tiktok", "youtube", "facebook", "telegram", "twitter", "linkedin"],
        priority=9,
    ),
]


class PublishingRouter:
    """Route content to platforms based on rules."""

    def __init__(self) -> None:
        self._rules: list[PublishRule] = []
        self._load()
        if not self._rules:
            self._rules = list(DEFAULT_RULES)
            self._save()

    def get_platforms(self, content: dict) -> list[str]:
        """Determine which platforms to publish to."""
        platforms: set[str] = set()
        for rule in self._rules:
            if rule.enabled and rule.matches(content):
                platforms.update(rule.target_platforms)

        # Fall back to Instagram if no rules match
        if not platforms:
            platforms.add("instagram")

        return sorted(platforms)

    def add_rule(self, **kwargs) -> PublishRule:
        rule = PublishRule(**kwargs)
        self._rules.append(rule)
        self._save()
        return rule

    def remove_rule(self, rule_id: str) -> bool:
        for rule in self._rules:
            if rule.id == rule_id:
                self._rules.remove(rule)
                self._save()
                return True
        return False

    def toggle_rule(self, rule_id: str) -> PublishRule | None:
        for rule in self._rules:
            if rule.id == rule_id:
                rule.enabled = not rule.enabled
                self._save()
                return rule
        return None

    def get_rules(self) -> list[PublishRule]:
        return list(self._rules)

    def display(self) -> str:
        lines = [
            "=" * 70,
            "  Publishing Rules",
            "=" * 70,
        ]

        for rule in self._rules:
            status = "ON " if rule.enabled else "OFF"
            platforms = ", ".join(rule.target_platforms)
            conditions = []
            if rule.content_type:
                conditions.append(f"type={rule.content_type}")
            if rule.category:
                conditions.append(f"cat={rule.category}")
            if rule.campaign_id:
                conditions.append(f"campaign={rule.campaign_id}")
            cond_str = " & ".join(conditions) if conditions else "all content"

            lines.append(
                f"  [{status}] {rule.id:<22} P{rule.priority} "
                f"  {cond_str}"
            )
            lines.append(f"        → {platforms}")

        lines.append("=" * 70)
        return "\n".join(lines)

    def _load(self) -> None:
        if RULES_FILE.exists():
            try:
                data = json.loads(RULES_FILE.read_text())
                self._rules = [PublishRule(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._rules = []

    def _save(self) -> None:
        RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(r) for r in self._rules]
        RULES_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
