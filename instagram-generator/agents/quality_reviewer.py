"""Quality Reviewer Agent (Контроль качества) — reviews and scores output.

The Quality Reviewer:
  - Scores content across multiple dimensions
  - Checks cultural sensitivity for Uzbek audience
  - Validates technical requirements (aspect ratio, duration, etc.)
  - Ensures brand consistency
  - Decides whether content needs revision or is ready to publish
"""

from __future__ import annotations

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

# Minimum scores for auto-approval
MIN_SCORES = {
    "visual_quality": 6.0,
    "caption_quality": 6.0,
    "brand_alignment": 6.0,
    "cultural_sensitivity": 8.0,  # High bar for cultural content
    "engagement_potential": 5.0,
    "technical_compliance": 7.0,
}

# Uzbek cultural sensitivity checks
SENSITIVE_TOPICS = [
    "religion", "politics", "alcohol", "gambling",
    "inappropriate imagery", "controversial opinions",
]

# Technical requirements
TECH_REQUIREMENTS = {
    "reel": {
        "aspect_ratio": "9:16",
        "max_duration_s": 90,
        "min_duration_s": 3,
        "max_file_size_mb": 250,
        "formats": ["mp4"],
        "max_caption_length": 2200,
        "max_hashtags": 30,
    },
    "image": {
        "aspect_ratios": ["1:1", "4:5", "1.91:1"],
        "min_resolution": (320, 320),
        "max_resolution": (1440, 1440),
        "max_file_size_mb": 8,
        "formats": ["jpg", "png"],
        "max_caption_length": 2200,
        "max_hashtags": 30,
    },
    "carousel": {
        "aspect_ratios": ["1:1", "4:5"],
        "min_slides": 2,
        "max_slides": 10,
        "max_file_size_mb": 8,
        "max_caption_length": 2200,
        "max_hashtags": 30,
    },
    "story": {
        "aspect_ratio": "9:16",
        "max_duration_s": 60,
        "max_file_size_mb": 250,
        "formats": ["jpg", "png", "mp4"],
    },
}


class QualityReviewerAgent(CreativeAgent):
    """Reviews content quality and decides on approval."""

    role = AgentRole.QUALITY_REVIEWER

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info("quality_reviewer.process", content_type=brief.content_type)

        scores = {}

        # 1. Score visual quality
        scores["visual_quality"] = self._score_visual(brief)

        # 2. Score caption quality
        scores["caption_quality"] = self._score_caption(brief)

        # 3. Score brand alignment
        scores["brand_alignment"] = self._score_brand(brief)

        # 4. Score cultural sensitivity
        scores["cultural_sensitivity"] = self._score_cultural(brief)

        # 5. Score engagement potential
        scores["engagement_potential"] = self._score_engagement(brief)

        # 6. Score technical compliance
        scores["technical_compliance"] = self._score_technical(brief)

        brief.quality_scores = scores

        # Decision
        avg_score = sum(scores.values()) / len(scores)
        all_above_min = all(
            scores.get(k, 0) >= v for k, v in MIN_SCORES.items()
        )

        if all_above_min and avg_score >= 7.0:
            brief.approved = True
            brief.revision_notes = ""
            logger.info("quality_reviewer.approved", scores=scores, avg=avg_score)
        else:
            brief.approved = False
            brief.revision_notes = self._generate_revision_notes(scores)
            logger.warning(
                "quality_reviewer.needs_revision",
                scores=scores,
                avg=avg_score,
                notes=brief.revision_notes,
            )

        return brief

    def _score_visual(self, brief: CreativeBrief) -> float:
        """Score visual quality of the prompt and style choices."""
        score = 5.0  # Base

        # Has detailed image prompt
        if len(brief.image_prompt) > 100:
            score += 1.0
        if len(brief.image_prompt) > 200:
            score += 0.5

        # Has lighting setup
        if brief.lighting_setup:
            score += 1.0

        # Has color palette
        if brief.color_palette and len(brief.color_palette) >= 3:
            score += 1.0

        # Has composition notes
        if brief.composition_notes:
            score += 0.5

        # Has negative prompt (prevents artifacts)
        if brief.negative_prompt:
            score += 1.0

        return min(score, 10.0)

    def _score_caption(self, brief: CreativeBrief) -> float:
        """Score caption quality."""
        score = 5.0

        caption = brief.caption or ""

        # Has content
        if len(caption) > 50:
            score += 1.0
        if len(caption) > 150:
            score += 0.5

        # Has hashtags
        if brief.hashtags and len(brief.hashtags) >= 5:
            score += 1.0
        if brief.hashtags and len(brief.hashtags) >= 10:
            score += 0.5

        # Has CTA
        if brief.cta:
            score += 1.0

        # Has hook line
        if brief.hook_line:
            score += 1.0

        # Not too long
        if len(caption) > 2200:
            score -= 2.0

        return min(max(score, 0.0), 10.0)

    def _score_brand(self, brief: CreativeBrief) -> float:
        """Score brand voice alignment."""
        score = 7.0  # Assume good by default

        # Check brand voice keywords in caption
        voice_keywords = brief.brand_voice.lower().split(", ")
        caption_lower = (brief.caption or "").lower()

        if brief.mood:
            score += 0.5

        # Consistency check — mood matches category expectations
        mood_category_match = {
            "motivational": ["inspiring", "energetic", "powerful"],
            "educational": ["professional", "trustworthy", "clear"],
            "product": ["premium", "modern", "quality"],
            "travel": ["adventurous", "cinematic", "beautiful"],
        }
        expected = mood_category_match.get(brief.category, [])
        mood_lower = (brief.mood or "").lower()
        if any(kw in mood_lower for kw in expected):
            score += 1.0

        return min(score, 10.0)

    def _score_cultural(self, brief: CreativeBrief) -> float:
        """Score cultural sensitivity for Uzbek audience."""
        score = 9.0  # Start high, deduct for issues

        all_text = " ".join([
            brief.caption or "",
            brief.voiceover_text or "",
            brief.image_prompt or "",
            brief.hook_line or "",
        ]).lower()

        # Check for sensitive topics
        for topic in SENSITIVE_TOPICS:
            if topic in all_text:
                score -= 2.0
                logger.warning("cultural_check.flag", topic=topic)

        # Bonus: uses Uzbek language
        uzbek_chars = set("o'g'sh")
        if any(c in all_text for c in ["o'", "g'", "sh"]):
            score += 0.5

        return min(max(score, 0.0), 10.0)

    def _score_engagement(self, brief: CreativeBrief) -> float:
        """Score engagement potential."""
        score = 5.0

        # Has hook (critical for Reels)
        if brief.hook_line:
            score += 1.5

        # Has CTA
        if brief.cta:
            score += 1.0

        # Hashtag reach
        if brief.hashtags:
            if len(brief.hashtags) >= 10:
                score += 1.0
            if len(brief.hashtags) >= 15:
                score += 0.5

        # Has voiceover (higher engagement for Reels)
        if brief.voiceover_text:
            score += 1.0

        return min(score, 10.0)

    def _score_technical(self, brief: CreativeBrief) -> float:
        """Score technical compliance with Instagram requirements."""
        score = 8.0  # Start high

        reqs = TECH_REQUIREMENTS.get(brief.content_type, {})

        # Caption length
        caption_len = len(brief.caption or "")
        max_caption = reqs.get("max_caption_length", 2200)
        if caption_len > max_caption:
            score -= 3.0

        # Hashtag count
        max_tags = reqs.get("max_hashtags", 30)
        if len(brief.hashtags) > max_tags:
            score -= 2.0

        # Carousel slide count
        if brief.content_type == "carousel":
            num_slides = len(brief.carousel_prompts)
            if num_slides < reqs.get("min_slides", 2):
                score -= 3.0
            if num_slides > reqs.get("max_slides", 10):
                score -= 3.0

        # Duration check for video
        if brief.content_type == "reel":
            dur = int(brief.duration or "5")
            if dur > reqs.get("max_duration_s", 90):
                score -= 3.0

        return min(max(score, 0.0), 10.0)

    def _generate_revision_notes(self, scores: dict[str, float]) -> str:
        """Generate specific revision notes for failed checks."""
        notes = []
        for metric, min_score in MIN_SCORES.items():
            actual = scores.get(metric, 0)
            if actual < min_score:
                notes.append(
                    f"- {metric}: {actual:.1f} (need {min_score:.1f}+)"
                )
        return "\n".join(notes) if notes else "General quality improvement needed"
