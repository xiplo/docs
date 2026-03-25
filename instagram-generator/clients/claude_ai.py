"""Claude AI client — powers all intelligent content generation.

Uses Claude claude-sonnet-4-6 for:
  - Creative content generation (captions, scripts, voiceover text)
  - Translation (uz → ru, uz → en)
  - Content quality review
  - Hashtag optimization
  - Audience analysis

All prompts use structured output with clear system instructions.
"""

from __future__ import annotations

import json
import os

import httpx
import structlog

logger = structlog.get_logger(__name__)

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6-20250514")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"


class ClaudeClient:
    """Anthropic Claude API client for content intelligence."""

    def __init__(self, api_key: str = "", model: str = "") -> None:
        self._api_key = api_key or CLAUDE_API_KEY
        self._model = model or CLAUDE_MODEL
        self._client = httpx.AsyncClient(
            timeout=120.0,
            headers={
                "x-api-key": self._api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
        )

    async def generate(
        self,
        system: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """Send a message to Claude and return the text response."""
        if not self._api_key:
            logger.warning("claude.no_api_key")
            return ""

        payload = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }

        resp = await self._client.post(CLAUDE_API_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()

        text = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                text += block["text"]

        logger.info(
            "claude.generated",
            model=self._model,
            input_tokens=data.get("usage", {}).get("input_tokens", 0),
            output_tokens=data.get("usage", {}).get("output_tokens", 0),
        )
        return text

    async def generate_json(
        self,
        system: str,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.5,
    ) -> dict:
        """Generate and parse a JSON response from Claude."""
        system_with_json = (
            f"{system}\n\n"
            "IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanation, no code fences."
        )
        text = await self.generate(system_with_json, prompt, max_tokens, temperature)

        # Strip markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("claude.json_parse_failed", text=text[:200])
            return {}

    async def close(self) -> None:
        await self._client.aclose()


# =====================================================================
# Pre-built system prompts for each use case
# =====================================================================

SYSTEM_PROMPTS = {
    "content_creator": """You are an expert Uzbek social media content creator.
You create viral, engaging content for Instagram, TikTok, YouTube, and other platforms.
Your audience is primarily Uzbek-speaking (18-35 age group) in Uzbekistan.

Key principles:
- Write captions in natural, conversational Uzbek
- Use emotional hooks that resonate with Uzbek culture
- Include call-to-actions that drive engagement
- Respect cultural values: family (oila), hard work (mehnat), respect (hurmat), tradition (an'ana)
- Avoid: political, religious, or ethnically sensitive content
- Mix Uzbek with occasional Russian/English words (as used naturally in Tashkent)""",

    "translator": """You are a professional translator specializing in Uzbek, Russian, and English.
You translate social media content while preserving:
- Emotional tone and impact
- Cultural references (adapt, don't just translate)
- Hashtag effectiveness per language
- Platform-specific conventions

Never produce literal translations. Adapt the message for the target audience.""",

    "quality_reviewer": """You are a senior content quality reviewer for social media.
You evaluate content on these criteria (score 1-10 each):
- visual_quality: Image/video prompt clarity and detail
- caption_quality: Hook strength, readability, emotional impact
- cultural_fit: Appropriateness for Uzbek audience
- engagement_potential: Likelihood of likes, comments, shares, saves
- brand_consistency: Tone, style, messaging alignment
- technical_quality: Caption length, hashtag count, format compliance

Return a JSON object with scores and specific improvement suggestions.""",

    "hashtag_optimizer": """You are a social media hashtag specialist for the Uzbek market.
Given a content topic and category, suggest optimal hashtags using the 30-15-5 strategy:
- 30% broad (>1M posts): for reach
- 15% mid (100K-1M posts): for discovery
- 5% niche (<100K posts): for targeted audience
Mix Uzbek, Russian, and English hashtags based on platform.
Return JSON with categorized hashtag arrays.""",

    "caption_writer": """You are an expert social media copywriter for the Uzbek market.
Write captions that:
- Start with a strong hook (question, bold statement, or story opener)
- Include 2-3 value points or emotional beats
- End with a clear CTA (call-to-action)
- Use appropriate emoji (not excessive)
- Stay within platform character limits
- Include a mix of Uzbek and contextual Russian/English phrases

Return JSON with: hook, body, cta, full_caption, hashtags""",

    "script_writer": """You are a professional video scriptwriter for short-form content.
Write scripts for 15-60 second videos optimized for:
- TikTok / Instagram Reels / YouTube Shorts format
- Uzbek-speaking audience
- Mobile-first viewing (vertical 9:16)

Structure: hook (0-3s), value (3-12s), climax (12-17s), CTA (17-20s)
Include: voiceover text, on-screen text cues, scene descriptions, music mood.
Return JSON with: scenes[], voiceover_text, subtitle_cues[], music_mood, total_duration_s""",

    "audience_analyzer": """You are a social media audience analyst specializing in the Uzbek market.
Analyze content performance patterns and suggest:
- Optimal posting times for Uzbekistan (Asia/Tashkent timezone)
- Content themes that resonate with the audience
- Engagement improvement strategies
- Audience growth tactics
Return structured JSON with actionable recommendations.""",
}
