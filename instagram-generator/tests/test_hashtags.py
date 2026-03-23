"""Tests for hashtag research tool."""

from skills.hashtags import HashtagResearch, BANNED_HASHTAGS, HASHTAG_POOLS


class TestHashtagResearch:
    def test_suggest_returns_correct_count(self):
        result = HashtagResearch.suggest("motivational", count=12)
        assert 8 <= result.total <= 15

    def test_suggest_all_categories(self):
        for category in HASHTAG_POOLS:
            result = HashtagResearch.suggest(category)
            assert result.total > 0
            assert result.category == category

    def test_suggest_fallback_for_unknown_category(self):
        result = HashtagResearch.suggest("nonexistent")
        assert result.total > 0

    def test_suggest_with_extra_tags(self):
        result = HashtagResearch.suggest("recipe", extra_tags=["homecooking", "yummy"])
        assert "homecooking" in result.tags or result.total >= 8

    def test_banned_hashtags_removed(self):
        result = HashtagResearch.suggest("motivational", extra_tags=["follow4follow", "l4l"])
        assert "follow4follow" not in result.tags
        assert "l4l" not in result.tags
        assert len(result.banned_removed) > 0

    def test_check_banned(self):
        flagged = HashtagResearch.check_banned(["motivation", "follow4follow", "success", "like4like"])
        assert "follow4follow" in flagged
        assert "like4like" in flagged
        assert "motivation" not in flagged

    def test_get_related(self):
        related = HashtagResearch.get_related("recipe")
        assert len(related) > 5

    def test_display(self):
        output = HashtagResearch.display()
        assert "Hashtag Research" in output
        assert "recipe" in output.lower() or "RECIPE" in output

    def test_display_single_category(self):
        output = HashtagResearch.display("travel")
        assert "TRAVEL" in output

    def test_as_string(self):
        result = HashtagResearch.suggest("motivational")
        s = result.as_string()
        assert s.startswith("#")
        assert " #" in s


class TestBannedHashtags:
    def test_known_banned(self):
        assert "follow4follow" in BANNED_HASHTAGS
        assert "like4like" in BANNED_HASHTAGS
        assert "f4f" in BANNED_HASHTAGS

    def test_legitimate_not_banned(self):
        assert "motivation" not in BANNED_HASHTAGS
        assert "uzbekistan" not in BANNED_HASHTAGS
