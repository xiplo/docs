"""AI-powered content generation — uses Claude for intelligent content creation.

Replaces rule-based agent logic with Claude claude-sonnet-4-6 for:
  - Caption generation (hook + body + CTA)
  - Script writing (scene-by-scene)
  - Translation (uz → ru/en with cultural adaptation)
  - Quality review (scored feedback)
  - Hashtag optimization (3-tier strategy)

Falls back to rule-based generation when API key is not set.
"""

from __future__ import annotations

import structlog

from clients.claude_ai import ClaudeClient, SYSTEM_PROMPTS

logger = structlog.get_logger(__name__)


class AIContentGenerator:
    """Generate content using Claude AI with fallback to rules."""

    def __init__(self) -> None:
        self._claude = ClaudeClient()

    @property
    def ai_enabled(self) -> bool:
        return bool(self._claude._api_key)

    async def generate_caption(
        self,
        topic: str,
        category: str,
        content_type: str = "reel",
        platform: str = "instagram",
        tone: str = "engaging",
    ) -> dict:
        """Generate a full caption with hook, body, CTA, and hashtags."""
        if not self.ai_enabled:
            return self._fallback_caption(topic, category)

        prompt = f"""Generate a {platform} caption for this content:

Topic: {topic}
Category: {category}
Content type: {content_type}
Tone: {tone}
Language: Uzbek (primary), with natural Russian/English mix

Return JSON:
{{
    "hook": "opening line that grabs attention",
    "body": "main caption text (2-3 sentences)",
    "cta": "call-to-action",
    "full_caption": "complete assembled caption",
    "hashtags": ["tag1", "tag2", ...],
    "emoji_count": 3
}}"""

        result = await self._claude.generate_json(
            SYSTEM_PROMPTS["caption_writer"], prompt, temperature=0.8
        )
        return result or self._fallback_caption(topic, category)

    async def generate_script(
        self,
        topic: str,
        category: str,
        duration: str = "15",
        style: str = "cinematic",
    ) -> dict:
        """Generate a video script with scenes, voiceover, and cues."""
        if not self.ai_enabled:
            return self._fallback_script(topic, category, duration)

        prompt = f"""Write a {duration}-second video script:

Topic: {topic}
Category: {category}
Style: {style}
Language: Uzbek voiceover
Format: Instagram Reel / TikTok / YouTube Short (9:16 vertical)

Return JSON:
{{
    "scenes": [
        {{"time": "0-3s", "description": "...", "on_screen_text": "...", "motion": "zoom_in"}}
    ],
    "voiceover_text": "Full Uzbek voiceover text",
    "subtitle_cues": ["cue1", "cue2"],
    "music_mood": "uplifting",
    "total_duration_s": {duration},
    "hook_line": "Opening hook text"
}}"""

        result = await self._claude.generate_json(
            SYSTEM_PROMPTS["script_writer"], prompt, temperature=0.7
        )
        return result or self._fallback_script(topic, category, duration)

    async def translate(
        self,
        text: str,
        source_lang: str = "uz",
        target_lang: str = "ru",
        category: str = "",
        platform: str = "instagram",
    ) -> dict:
        """Translate content with cultural adaptation."""
        if not self.ai_enabled:
            return {"translation": text, "hashtags": [], "adapted": False}

        lang_names = {"uz": "Uzbek", "ru": "Russian", "en": "English"}

        prompt = f"""Translate this {lang_names.get(source_lang, source_lang)} social media caption to {lang_names.get(target_lang, target_lang)}:

Original text:
{text}

Category: {category}
Platform: {platform}

Adapt culturally for the {lang_names.get(target_lang)} audience. Don't translate literally.

Return JSON:
{{
    "translation": "translated and adapted caption",
    "hashtags": ["localized_hashtag1", "hashtag2"],
    "notes": "what was adapted and why"
}}"""

        result = await self._claude.generate_json(
            SYSTEM_PROMPTS["translator"], prompt, temperature=0.5
        )
        if result:
            result["adapted"] = True
        return result or {"translation": text, "hashtags": [], "adapted": False}

    async def review_content(
        self,
        caption: str,
        image_prompt: str = "",
        hashtags: list[str] | None = None,
        content_type: str = "reel",
        category: str = "",
    ) -> dict:
        """AI-powered content quality review with scores and feedback."""
        if not self.ai_enabled:
            return self._fallback_review(caption, hashtags)

        prompt = f"""Review this social media content for an Uzbek audience:

Caption: {caption}
Image/Video prompt: {image_prompt}
Hashtags: {', '.join(hashtags or [])}
Content type: {content_type}
Category: {category}

Score each dimension 1-10 and provide specific improvement suggestions.

Return JSON:
{{
    "scores": {{
        "visual_quality": 8,
        "caption_quality": 7,
        "cultural_fit": 9,
        "engagement_potential": 7,
        "brand_consistency": 8,
        "technical_quality": 8
    }},
    "overall_score": 7.8,
    "approved": true,
    "suggestions": ["suggestion1", "suggestion2"],
    "improved_caption": "optional improved version",
    "improved_hashtags": ["better_tag1"]
}}"""

        result = await self._claude.generate_json(
            SYSTEM_PROMPTS["quality_reviewer"], prompt, temperature=0.3
        )
        return result or self._fallback_review(caption, hashtags)

    async def optimize_hashtags(
        self,
        topic: str,
        category: str,
        platform: str = "instagram",
        count: int = 15,
    ) -> dict:
        """AI-optimized hashtag selection."""
        if not self.ai_enabled:
            return self._fallback_hashtags(topic, category)

        prompt = f"""Suggest {count} optimal hashtags for this {platform} post:

Topic: {topic}
Category: {category}
Target audience: Uzbek-speaking, 18-35, in Uzbekistan

Use the 30-15-5 strategy:
- Broad hashtags (>1M posts): for maximum reach
- Mid hashtags (100K-1M): for discovery
- Niche hashtags (<100K): for targeted Uzbek audience

Mix Uzbek, Russian, and English hashtags.

Return JSON:
{{
    "broad": ["hashtag1", "hashtag2"],
    "mid": ["hashtag3", "hashtag4"],
    "niche": ["hashtag5", "hashtag6"],
    "all": ["all", "hashtags", "combined"],
    "banned_check": ["any_risky_tags"]
}}"""

        result = await self._claude.generate_json(
            SYSTEM_PROMPTS["hashtag_optimizer"], prompt, temperature=0.5
        )
        return result or self._fallback_hashtags(topic, category)

    async def close(self) -> None:
        await self._claude.close()

    # ------------------------------------------------------------------
    # Fallbacks (rule-based, used when API key is not set)
    # ------------------------------------------------------------------

    @staticmethod
    def _fallback_caption(topic: str, category: str) -> dict:
        hooks = {
            "motivational": "Bilasizmi?",
            "recipe": "Bugun tayyorlaymiz!",
            "travel": "Bu joyni ko'rdingizmi?",
        }
        ctas = {
            "motivational": "Obuna bo'ling!",
            "recipe": "Retseptni saqlang!",
            "travel": "Do'stlaringiz bilan ulashing!",
        }
        hook = hooks.get(category, "Qiziq!")
        cta = ctas.get(category, "Fikringizni yozing!")
        return {
            "hook": hook,
            "body": topic,
            "cta": cta,
            "full_caption": f"{hook}\n\n{topic}\n\n{cta}",
            "hashtags": [category, "uzbekistan", "tashkent"],
        }

    @staticmethod
    def _fallback_script(topic: str, category: str, duration: str) -> dict:
        return {
            "scenes": [
                {"time": "0-3s", "description": "Hook shot", "on_screen_text": topic[:30], "motion": "zoom_in"},
                {"time": f"3-{int(duration) - 3}s", "description": "Main content", "motion": "pan"},
                {"time": f"{int(duration) - 3}-{duration}s", "description": "CTA", "motion": "fade"},
            ],
            "voiceover_text": f"{topic}. Obuna bo'ling!",
            "music_mood": "uplifting",
            "total_duration_s": int(duration),
            "hook_line": topic[:50],
        }

    @staticmethod
    def _fallback_review(caption: str, hashtags: list[str] | None) -> dict:
        score = 7.0
        if len(caption) > 100:
            score += 0.5
        if hashtags and len(hashtags) >= 5:
            score += 0.5
        return {
            "scores": {
                "visual_quality": 7.0,
                "caption_quality": score,
                "cultural_fit": 8.0,
                "engagement_potential": 6.5,
                "brand_consistency": 7.0,
                "technical_quality": 7.5,
            },
            "overall_score": score,
            "approved": score >= 7.0,
            "suggestions": ["Add more hashtags" if not hashtags else "Content looks good"],
        }

    @staticmethod
    def _fallback_hashtags(topic: str, category: str) -> dict:
        from skills.hashtags import HashtagResearch
        result = HashtagResearch.suggest(category)
        return {
            "broad": result.tags[:4],
            "mid": result.tags[4:8],
            "niche": result.tags[8:],
            "all": result.tags,
        }
