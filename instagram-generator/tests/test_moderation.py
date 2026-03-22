"""Tests for content moderation system."""

from __future__ import annotations

import pytest

from skills.moderation import ContentModerator, ModerationResult


class TestTextModeration:
    def test_clean_text_passes(self):
        result = ContentModerator.check_text(
            "Bugun yangi kun — yangi imkoniyatlar! Oila va mehnat bilan muvaffaqiyatga erishamiz."
        )
        assert result.passed is True
        assert result.score > 0.7

    def test_empty_text_passes(self):
        result = ContentModerator.check_text("")
        assert result.passed is True
        assert result.score == 1.0

    def test_blocked_content_fails(self):
        result = ContentModerator.check_text("This is a scam, hack your way to success")
        assert result.passed is False
        assert any("blocked_content" in f for f in result.flags)

    def test_instagram_restricted_flagged(self):
        result = ContentModerator.check_text("Follow me! #follow4follow #like4like")
        assert any("instagram_restricted" in f for f in result.flags)

    def test_cultural_sensitivity_flagged(self):
        result = ContentModerator.check_text("Siyosat haqida fikr")
        assert any("sensitive_topic:politics" in f for f in result.flags)

    def test_positive_cultural_markers_boost(self):
        # Text with positive markers should score higher
        base = ContentModerator.check_text("Oddiy matn hech narsasiz")
        boosted = ContentModerator.check_text(
            "Oila va mehnat — hurmat va an'ana bilan"
        )
        assert boosted.score >= base.score

    def test_excessive_caps_flagged(self):
        result = ContentModerator.check_text("BUGUN JUDA KATTA VOQEA BOLDI HAMMA KELING!")
        assert any("excessive_caps" in f for f in result.flags)

    def test_long_caption_flagged(self):
        result = ContentModerator.check_text("A" * 2500)
        assert any("caption_too_long" in f for f in result.flags)


class TestHashtagModeration:
    def test_normal_hashtags_pass(self):
        result = ContentModerator.check_hashtags(
            ["motivatsiya", "uzbekistan", "tashkent", "hayot"]
        )
        assert result.passed is True

    def test_too_many_hashtags(self):
        result = ContentModerator.check_hashtags([f"tag{i}" for i in range(35)])
        assert any("too_many_hashtags" in f for f in result.flags)

    def test_banned_hashtags(self):
        result = ContentModerator.check_hashtags(["follow4follow", "l4l", "spam"])
        assert result.passed is False
        assert len([f for f in result.flags if "banned_hashtag" in f]) >= 2


class TestFullModeration:
    def test_clean_content_passes(self):
        result = ContentModerator.check_content_request(
            caption="Yangi kun, yangi imkoniyatlar!",
            hashtags=["motivatsiya", "uzbek"],
            voiceover="Bugun ajoyib kun boladi.",
        )
        assert result.passed is True
        assert result.score > 0.7

    def test_blocked_caption_blocks_all(self):
        result = ContentModerator.check_content_request(
            caption="This is a fraud scheme, gambling casino",
            hashtags=["success"],
        )
        assert result.passed is False

    def test_summary_format(self):
        result = ModerationResult(
            passed=True, score=0.95, flags=[], suggestions=[]
        )
        assert "PASSED" in result.summary
        assert "95" in result.summary
