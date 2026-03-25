"""Tests for AI content generation (fallback mode without API key)."""

import pytest

from skills.ai_content import AIContentGenerator


@pytest.fixture
def gen():
    return AIContentGenerator()


class TestAIContentGenerator:
    def test_ai_disabled_without_key(self, gen):
        assert gen.ai_enabled is False

    @pytest.mark.asyncio
    async def test_fallback_caption(self, gen):
        result = await gen.generate_caption("Palov recipe", "recipe")
        assert "hook" in result
        assert "full_caption" in result
        assert result["hashtags"]

    @pytest.mark.asyncio
    async def test_fallback_script(self, gen):
        result = await gen.generate_script("Morning motivation", "motivational", "15")
        assert "scenes" in result
        assert len(result["scenes"]) >= 2
        assert "voiceover_text" in result

    @pytest.mark.asyncio
    async def test_fallback_review(self, gen):
        result = await gen.review_content(
            "Test caption for review",
            hashtags=["test", "review", "uzbek", "tashkent", "motivation"],
        )
        assert "scores" in result
        assert "overall_score" in result
        assert result["approved"] is True

    @pytest.mark.asyncio
    async def test_fallback_hashtags(self, gen):
        result = await gen.optimize_hashtags("Palov recipe", "recipe")
        assert "broad" in result
        assert "all" in result
        assert len(result["all"]) > 0

    @pytest.mark.asyncio
    async def test_fallback_translate(self, gen):
        result = await gen.translate("Test text", "uz", "ru")
        assert "translation" in result
        assert result["adapted"] is False


class TestClaudeSystemPrompts:
    def test_all_prompts_defined(self):
        from clients.claude_ai import SYSTEM_PROMPTS
        expected = [
            "content_creator", "translator", "quality_reviewer",
            "hashtag_optimizer", "caption_writer", "script_writer",
            "audience_analyzer",
        ]
        for key in expected:
            assert key in SYSTEM_PROMPTS, f"Missing prompt: {key}"
            assert len(SYSTEM_PROMPTS[key]) > 100, f"Prompt too short: {key}"
