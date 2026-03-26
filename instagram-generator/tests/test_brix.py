"""Tests for BRIX.UZ brand profile and content briefs."""

from brands.brix_uz import (
    BrixBrandProfile,
    VIRAL_CONTENT_BRIEFS,
    get_all_briefs,
    get_brief_by_id,
    get_briefs_by_category,
)


class TestBrixBrandProfile:
    def test_profile_defaults(self):
        profile = BrixBrandProfile()
        assert profile.name == "BRIX.UZ"
        assert len(profile.colors) == 4
        assert len(profile.products) >= 10
        assert "instagram" in profile.platforms
        assert "tiktok" in profile.platforms

    def test_profile_hashtags(self):
        profile = BrixBrandProfile()
        assert "brixuz" in profile.hashtags
        assert len(profile.hashtags) == 5  # Instagram 5-hashtag cap


class TestViralContentBriefs:
    def test_briefs_exist(self):
        assert len(VIRAL_CONTENT_BRIEFS) >= 8

    def test_all_briefs_have_required_fields(self):
        required = ["id", "topic", "category", "content_type", "duration",
                     "image_prompt", "caption_uz", "voiceover_uz", "hook"]
        for brief in VIRAL_CONTENT_BRIEFS:
            for field in required:
                assert field in brief, f"Brief {brief.get('id', '?')} missing {field}"

    def test_all_reels(self):
        for brief in VIRAL_CONTENT_BRIEFS:
            assert brief["content_type"] == "reel"

    def test_get_by_id(self):
        brief = get_brief_by_id("brix_01_forklift_dance")
        assert brief is not None
        assert "forklift" in brief["topic"].lower()

    def test_get_by_id_not_found(self):
        assert get_brief_by_id("nonexistent") is None

    def test_get_by_category(self):
        satisfying = get_briefs_by_category("satisfying_machinery")
        assert len(satisfying) >= 3

    def test_get_all(self):
        all_briefs = get_all_briefs()
        assert len(all_briefs) == len(VIRAL_CONTENT_BRIEFS)

    def test_image_prompts_are_detailed(self):
        for brief in VIRAL_CONTENT_BRIEFS:
            assert len(brief["image_prompt"]) > 100, f"Image prompt too short: {brief['id']}"

    def test_video_prompts_exist(self):
        for brief in VIRAL_CONTENT_BRIEFS:
            if "video_prompt" in brief:
                assert len(brief["video_prompt"]) > 50

    def test_hooks_are_engaging(self):
        for brief in VIRAL_CONTENT_BRIEFS:
            hook = brief["hook"]
            assert len(hook) > 10
            # Should end with emoji or punctuation
            assert hook[-1] in "!?😱😍🤯📈👀👷🤔⚠️"

    def test_captions_have_hashtags(self):
        for brief in VIRAL_CONTENT_BRIEFS:
            assert "#brixuz" in brief["caption_uz"]

    def test_duration_is_valid(self):
        for brief in VIRAL_CONTENT_BRIEFS:
            dur = int(brief["duration"])
            assert 3 <= dur <= 60
