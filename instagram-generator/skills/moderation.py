"""Content moderation — safety and cultural sensitivity checks.

Validates content before publishing:
  1. Text moderation (captions, voiceover scripts)
  2. Cultural sensitivity for Uzbek audience
  3. Instagram community guidelines compliance
  4. Brand safety checks
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ModerationResult:
    """Result of a content moderation check."""

    passed: bool
    score: float  # 0.0 - 1.0 (1.0 = fully safe)
    flags: list[str]
    suggestions: list[str]

    @property
    def summary(self) -> str:
        status = "PASSED" if self.passed else "BLOCKED"
        return f"[{status}] Score: {self.score:.1%} | Flags: {len(self.flags)}"


# Cultural sensitivity patterns for Uzbek content
CULTURAL_SENSITIVE_TOPICS = {
    "religion": [
        r"\bdin\b", r"\bislom\b", r"\bmasjid\b", r"\bnamoz\b",
        r"\bro'za\b", r"\bhaj\b", r"\bqur'on\b",
    ],
    "politics": [
        r"\bsiyosat\b", r"\bhukumat\b", r"\bprezident\b",
        r"\bpartiya\b", r"\btanqid\b",
    ],
    "ethnicity": [
        r"\bmillat\b", r"\birq\b", r"\betnik\b",
    ],
}

# Words/phrases to avoid in Instagram content
BLOCKED_PATTERNS = [
    r"\b(fraud|scam|ponzi)\b",
    r"\b(hack|crack|pirat)\b",
    r"(casino|gambling|qimor)",
    r"(18\+|xxx|adult)",
    r"(drug|narkotik|giyoh)",
]

# Instagram-specific restrictions
INSTAGRAM_RESTRICTED = [
    r"#follow4follow",
    r"#like4like",
    r"#f4f",
    r"#l4l",
    r"DM\s+me\s+for",
    r"link\s+in\s+bio",  # Not blocked but flagged for overuse
]

# Uzbek cultural values to reinforce
POSITIVE_CULTURAL_MARKERS = [
    "oila",  # family
    "mehnat",  # hard work
    "hurmat",  # respect
    "an'ana",  # tradition
    "vatanparvarlik",  # patriotism
    "ilm",  # knowledge
    "do'stlik",  # friendship
    "mehmondo'stlik",  # hospitality
]


class ContentModerator:
    """Validates content safety and cultural appropriateness."""

    SAFETY_THRESHOLD = 0.7  # Minimum score to pass

    @classmethod
    def check_text(cls, text: str) -> ModerationResult:
        """Moderate text content (captions, scripts, voiceover)."""
        flags = []
        suggestions = []
        score = 1.0

        if not text or not text.strip():
            return ModerationResult(passed=True, score=1.0, flags=[], suggestions=[])

        text_lower = text.lower()

        # Check blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                flags.append(f"blocked_content: {pattern}")
                score -= 0.3

        # Check Instagram restrictions
        for pattern in INSTAGRAM_RESTRICTED:
            if re.search(pattern, text_lower, re.IGNORECASE):
                flags.append(f"instagram_restricted: {pattern}")
                score -= 0.1
                suggestions.append(
                    "Instagram may reduce reach for engagement-bait patterns"
                )

        # Cultural sensitivity check
        for topic, patterns in CULTURAL_SENSITIVE_TOPICS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    flags.append(f"sensitive_topic:{topic}")
                    score -= 0.15
                    suggestions.append(
                        f"Content touches on '{topic}' — ensure respectful treatment"
                    )
                    break  # One flag per topic

        # Length checks
        if len(text) > 2200:
            flags.append("caption_too_long")
            suggestions.append("Instagram caption max is 2200 characters")
            score -= 0.1

        # Positive cultural markers boost
        cultural_matches = sum(
            1 for marker in POSITIVE_CULTURAL_MARKERS if marker in text_lower
        )
        if cultural_matches > 0:
            score = min(1.0, score + cultural_matches * 0.05)

        # Excessive caps check
        if text.isupper() and len(text) > 20:
            flags.append("excessive_caps")
            suggestions.append("Avoid ALL CAPS — it reads as shouting")
            score -= 0.05

        # Excessive emoji check
        emoji_count = len(re.findall(r"[\U00010000-\U0010ffff]", text))
        if emoji_count > 15:
            flags.append("excessive_emojis")
            suggestions.append("Too many emojis can reduce perceived quality")
            score -= 0.05

        score = max(0.0, min(1.0, score))
        passed = score >= cls.SAFETY_THRESHOLD and not any(
            "blocked_content" in f for f in flags
        )

        if not passed:
            logger.warning("moderation.blocked", score=score, flags=flags)

        return ModerationResult(
            passed=passed,
            score=score,
            flags=flags,
            suggestions=suggestions,
        )

    @classmethod
    def check_hashtags(cls, hashtags: list[str]) -> ModerationResult:
        """Validate hashtags for safety and strategy."""
        flags = []
        suggestions = []
        score = 1.0

        if len(hashtags) > 30:
            flags.append("too_many_hashtags")
            suggestions.append("Instagram allows max 30 hashtags")
            score -= 0.2

        if len(hashtags) < 3:
            suggestions.append("Consider using 10-20 hashtags for better reach")

        banned_tags = {"follow4follow", "like4like", "f4f", "l4l", "spam", "free"}
        for tag in hashtags:
            clean = tag.strip("#").lower()
            if clean in banned_tags:
                flags.append(f"banned_hashtag:#{clean}")
                score -= 0.15

        score = max(0.0, score)
        return ModerationResult(
            passed=score >= cls.SAFETY_THRESHOLD,
            score=score,
            flags=flags,
            suggestions=suggestions,
        )

    @classmethod
    def check_content_request(cls, caption: str, hashtags: list[str],
                               voiceover: str = "") -> ModerationResult:
        """Full content moderation — combines text + hashtag checks."""
        text_result = cls.check_text(caption)
        hashtag_result = cls.check_hashtags(hashtags)
        voiceover_result = cls.check_text(voiceover) if voiceover else ModerationResult(
            passed=True, score=1.0, flags=[], suggestions=[]
        )

        combined_flags = text_result.flags + hashtag_result.flags + voiceover_result.flags
        combined_suggestions = (
            text_result.suggestions + hashtag_result.suggestions + voiceover_result.suggestions
        )
        combined_score = (
            text_result.score * 0.5
            + hashtag_result.score * 0.2
            + voiceover_result.score * 0.3
        )

        passed = all([text_result.passed, hashtag_result.passed, voiceover_result.passed])

        return ModerationResult(
            passed=passed,
            score=combined_score,
            flags=combined_flags,
            suggestions=list(dict.fromkeys(combined_suggestions)),  # dedupe
        )
