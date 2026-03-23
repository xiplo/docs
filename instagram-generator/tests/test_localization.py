"""Tests for multi-language caption localization."""

from skills.localization import CaptionLocalizer, LANGUAGE_PROFILES, LOCALIZED_HASHTAGS


class TestCaptionLocalizer:
    def test_localize_basic(self):
        result = CaptionLocalizer.localize(
            "Har bir yangi kun — yangi imkoniyat!",
            category="motivational",
        )
        assert result.uz
        assert result.ru
        assert result.en

    def test_localize_with_cta(self):
        result = CaptionLocalizer.localize(
            "Palov tayyorlash!",
            category="recipe",
            include_cta=True,
            cta_type="save",
        )
        assert "Saqlab" in result.uz

    def test_localize_specific_languages(self):
        result = CaptionLocalizer.localize(
            "Test",
            target_langs=["uz", "en"],
        )
        assert result.uz
        assert result.en
        assert result.ru == ""  # Not requested

    def test_localized_hashtags(self):
        result = CaptionLocalizer.localize("Test", category="recipe")
        assert len(result.hashtags_uz) > 0
        assert len(result.hashtags_ru) > 0
        assert len(result.hashtags_en) > 0

    def test_get_profile(self):
        profile = CaptionLocalizer.get_profile("uz")
        assert "greeting" in profile
        assert profile["greeting"] == "Assalomu alaykum!"

    def test_display(self):
        output = CaptionLocalizer.display()
        assert "Multi-Language" in output
        assert "English" in output
        assert "Русский" in output

    def test_all_languages_have_profiles(self):
        for lang in CaptionLocalizer.SUPPORTED_LANGUAGES:
            assert lang in LANGUAGE_PROFILES
            assert lang in LOCALIZED_HASHTAGS
