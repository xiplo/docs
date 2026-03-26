"""Quality Reviewer Agent v2 — AI-powered quality review with rule fallback.

Uses Claude claude-sonnet-4-6 for intelligent content review when available.
Falls back to comprehensive rule-based scoring.

Quality dimensions (scored 1-10):
  - visual_quality: Image/video prompt detail and clarity
  - caption_quality: Hook, readability, emotional impact
  - brand_alignment: Tone, voice consistency
  - cultural_sensitivity: Uzbek cultural appropriateness (HIGH bar: 8.0+)
  - engagement_potential: Viral potential, save-worthiness
  - technical_compliance: Platform spec compliance
"""

from __future__ import annotations

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

MIN_SCORES = {
    "visual_quality": 6.0,
    "caption_quality": 6.0,
    "brand_alignment": 6.0,
    "cultural_sensitivity": 8.0,
    "engagement_potential": 5.0,
    "technical_compliance": 7.0,
}

SENSITIVE_TOPICS = [
    "religion", "politics", "alcohol", "gambling",
    "inappropriate imagery", "controversial opinions",
]

TECH_REQUIREMENTS = {
    "reel": {"max_caption_length": 2200, "max_hashtags": 30, "max_duration_s": 90, "min_duration_s": 3},
    "image": {"max_caption_length": 2200, "max_hashtags": 30},
    "carousel": {"max_caption_length": 2200, "max_hashtags": 30, "min_slides": 2, "max_slides": 10},
    "story": {"max_duration_s": 60},
}


class QualityReviewerAgent(CreativeAgent):
    """Reviews content quality — AI-first with rule-based fallback."""

    role = AgentRole.QUALITY_REVIEWER

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info("quality_reviewer.process", content_type=brief.content_type)

        # Try AI review first
        ai_review = await self._try_ai_review(brief)

        if ai_review and "scores" in ai_review:
            scores = ai_review["scores"]
            # Ensure all required dimensions exist
            for key in MIN_SCORES:
                if key not in scores:
                    scores[key] = 7.0
            brief.quality_scores = scores

            if ai_review.get("improved_caption"):
                brief.caption = ai_review["improved_caption"]
            if ai_review.get("improved_hashtags"):
                brief.hashtags = ai_review["improved_hashtags"]

            logger.info("quality_reviewer.ai_scored", scores=scores)
        else:
            # Rule-based scoring fallback
            scores = {
                "visual_quality": self._score_visual(brief),
                "caption_quality": self._score_caption(brief),
                "brand_alignment": self._score_brand(brief),
                "cultural_sensitivity": self._score_cultural(brief),
                "engagement_potential": self._score_engagement(brief),
                "technical_compliance": self._score_technical(brief),
            }
            brief.quality_scores = scores

        # Decision
        avg_score = sum(brief.quality_scores.values()) / len(brief.quality_scores)
        all_above_min = all(
            brief.quality_scores.get(k, 0) >= v for k, v in MIN_SCORES.items()
        )

        if all_above_min and avg_score >= 7.0:
            brief.approved = True
            brief.revision_notes = ""
            logger.info("quality_reviewer.approved", avg=avg_score)
        else:
            brief.approved = False
            brief.revision_notes = self._generate_revision_notes(brief.quality_scores)
            logger.warning("quality_reviewer.needs_revision", avg=avg_score)

        return brief

    async def _try_ai_review(self, brief: CreativeBrief) -> dict | None:
        """Try AI-powered quality review via Claude."""
        try:
            from skills.ai_content import AIContentGenerator

            gen = AIContentGenerator()
            if not gen.ai_enabled:
                return None

            result = await gen.review_content(
                caption=brief.caption,
                image_prompt=brief.image_prompt,
                hashtags=brief.hashtags,
                content_type=brief.content_type,
                category=brief.category,
            )
            await gen.close()
            return result

        except Exception as exc:
            logger.warning("quality_reviewer.ai_failed", error=str(exc))
            return None

    # ------------------------------------------------------------------
    # Rule-based scoring (fallback)
    # ------------------------------------------------------------------

    def _score_visual(self, brief: CreativeBrief) -> float:
        score = 5.0
        if len(brief.image_prompt) > 100:
            score += 1.0
        if len(brief.image_prompt) > 200:
            score += 0.5
        if brief.lighting_setup:
            score += 1.0
        if brief.color_palette and len(brief.color_palette) >= 3:
            score += 1.0
        if brief.composition_notes:
            score += 0.5
        if brief.negative_prompt:
            score += 1.0
        return min(score, 10.0)

    def _score_caption(self, brief: CreativeBrief) -> float:
        score = 5.0
        caption = brief.caption or ""
        if len(caption) > 50:
            score += 1.0
        if len(caption) > 150:
            score += 0.5
        if brief.hashtags and len(brief.hashtags) >= 5:
            score += 1.0
        if brief.cta:
            score += 1.0
        if brief.hook_line:
            score += 1.0
        if len(caption) > 2200:
            score -= 2.0
        return min(max(score, 0.0), 10.0)

    def _score_brand(self, brief: CreativeBrief) -> float:
        score = 7.0
        if brief.mood:
            score += 0.5
        mood_match = {
            "motivational": ["inspiring", "energetic", "powerful"],
            "educational": ["professional", "trustworthy", "clear"],
            "travel": ["adventurous", "cinematic", "beautiful"],
        }
        expected = mood_match.get(brief.category, [])
        mood_lower = (brief.mood or "").lower()
        if any(kw in mood_lower for kw in expected):
            score += 1.0
        return min(score, 10.0)

    def _score_cultural(self, brief: CreativeBrief) -> float:
        score = 9.0
        all_text = " ".join([
            brief.caption or "", brief.voiceover_text or "",
            brief.image_prompt or "", brief.hook_line or "",
        ]).lower()
        for topic in SENSITIVE_TOPICS:
            if topic in all_text:
                score -= 2.0
        return min(max(score, 0.0), 10.0)

    def _score_engagement(self, brief: CreativeBrief) -> float:
        score = 5.0
        if brief.hook_line:
            score += 1.5
        if brief.cta:
            score += 1.0
        if brief.hashtags and len(brief.hashtags) >= 5:
            score += 1.0
        if brief.voiceover_text:
            score += 1.0
        return min(score, 10.0)

    def _score_technical(self, brief: CreativeBrief) -> float:
        score = 8.0
        reqs = TECH_REQUIREMENTS.get(brief.content_type, {})
        if len(brief.caption or "") > reqs.get("max_caption_length", 2200):
            score -= 3.0
        if len(brief.hashtags) > reqs.get("max_hashtags", 30):
            score -= 2.0
        if brief.content_type == "carousel":
            n = len(brief.carousel_prompts)
            if n < reqs.get("min_slides", 2) or n > reqs.get("max_slides", 10):
                score -= 3.0
        if brief.content_type == "reel":
            dur = int(brief.duration or "5")
            if dur > reqs.get("max_duration_s", 90):
                score -= 3.0
        return min(max(score, 0.0), 10.0)

    def _generate_revision_notes(self, scores: dict[str, float]) -> str:
        notes = []
        for metric, min_score in MIN_SCORES.items():
            actual = scores.get(metric, 0)
            if actual < min_score:
                notes.append(f"- {metric}: {actual:.1f} (need {min_score:.1f}+)")
        return "\n".join(notes) if notes else "General quality improvement needed"
