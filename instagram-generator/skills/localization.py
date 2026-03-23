"""Multi-language caption generation — Uzbek, Russian, English.

Generates platform-adapted captions in multiple languages:
  - Uzbek (primary) — native audience
  - Russian — bilingual audience in Uzbekistan
  - English — international reach

Each language has its own:
  - Tone and register
  - Hashtag pool
  - Character limits per platform
  - CTA style
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LocalizedCaption:
    """Caption in multiple languages."""

    uz: str = ""
    ru: str = ""
    en: str = ""
    hashtags_uz: list[str] = field(default_factory=list)
    hashtags_ru: list[str] = field(default_factory=list)
    hashtags_en: list[str] = field(default_factory=list)

    def get(self, lang: str) -> str:
        return getattr(self, lang, self.uz)

    def get_hashtags(self, lang: str) -> list[str]:
        return getattr(self, f"hashtags_{lang}", self.hashtags_uz)


# Common translations and patterns per language
LANGUAGE_PROFILES = {
    "uz": {
        "name": "O'zbek tili",
        "cta_follow": "Obuna bo'ling!",
        "cta_like": "Yoqtiring va ulashing!",
        "cta_save": "Saqlab qo'ying!",
        "cta_comment": "Fikringizni yozing!",
        "cta_share": "Do'stlaringiz bilan ulashing!",
        "greeting": "Assalomu alaykum!",
        "farewell": "Omad tilaymiz!",
        "hook_question": "Bilasizmi?",
        "hook_number": "5 ta muhim maslahat",
        "hook_story": "Mana qanday qilib...",
    },
    "ru": {
        "name": "Русский",
        "cta_follow": "Подписывайтесь!",
        "cta_like": "Ставьте лайк и делитесь!",
        "cta_save": "Сохраняйте!",
        "cta_comment": "Напишите свое мнение!",
        "cta_share": "Поделитесь с друзьями!",
        "greeting": "Привет!",
        "farewell": "Удачи вам!",
        "hook_question": "Знаете ли вы?",
        "hook_number": "5 важных советов",
        "hook_story": "Вот как это работает...",
    },
    "en": {
        "name": "English",
        "cta_follow": "Follow for more!",
        "cta_like": "Like & share!",
        "cta_save": "Save this for later!",
        "cta_comment": "Drop your thoughts below!",
        "cta_share": "Share with your friends!",
        "greeting": "Hey there!",
        "farewell": "Good luck!",
        "hook_question": "Did you know?",
        "hook_number": "5 essential tips",
        "hook_story": "Here's how it works...",
    },
}

# Platform-specific hashtag pools per language
LOCALIZED_HASHTAGS = {
    "uz": {
        "motivational": ["motivatsiya", "muvaffaqiyat", "mehnat", "sabr", "ilhom"],
        "recipe": ["ozbektaomi", "palov", "taom", "retsept", "oshpaz"],
        "travel": ["uzbekistan", "sayohat", "toshkent", "samarqand", "buxoro"],
        "lifestyle": ["hayot", "turmush", "kundalik", "oilaviy", "soglomhayot"],
    },
    "ru": {
        "motivational": ["мотивация", "успех", "развитие", "бизнес", "цель"],
        "recipe": ["узбекскаякухня", "плов", "рецепт", "самса", "готовка"],
        "travel": ["узбекистан", "путешествие", "ташкент", "самарканд", "бухара"],
        "lifestyle": ["жизнь", "стиль", "здоровье", "утро", "семья"],
    },
    "en": {
        "motivational": ["motivation", "success", "mindset", "hustle", "goals"],
        "recipe": ["uzbekfood", "centralasianfood", "plov", "homecooking", "recipe"],
        "travel": ["uzbekistan", "centralasia", "silkroad", "travelasia", "explore"],
        "lifestyle": ["lifestyle", "dailylife", "morningroutine", "healthy", "wellness"],
    },
}


class CaptionLocalizer:
    """Generate and adapt captions in multiple languages."""

    SUPPORTED_LANGUAGES = ("uz", "ru", "en")

    @classmethod
    def localize(
        cls,
        caption_uz: str,
        category: str = "",
        include_cta: bool = True,
        cta_type: str = "follow",
        target_langs: list[str] | None = None,
    ) -> LocalizedCaption:
        """Create localized versions of a caption."""
        langs = target_langs or list(cls.SUPPORTED_LANGUAGES)
        result = LocalizedCaption(uz=caption_uz)

        # Add CTA to Uzbek
        if include_cta:
            cta_uz = LANGUAGE_PROFILES["uz"].get(f"cta_{cta_type}", "")
            if cta_uz and cta_uz not in caption_uz:
                result.uz = f"{caption_uz}\n\n{cta_uz}"

        # Generate Russian version
        if "ru" in langs:
            result.ru = cls._translate_to_ru(caption_uz, category)
            if include_cta:
                cta_ru = LANGUAGE_PROFILES["ru"].get(f"cta_{cta_type}", "")
                if cta_ru:
                    result.ru = f"{result.ru}\n\n{cta_ru}"

        # Generate English version
        if "en" in langs:
            result.en = cls._translate_to_en(caption_uz, category)
            if include_cta:
                cta_en = LANGUAGE_PROFILES["en"].get(f"cta_{cta_type}", "")
                if cta_en:
                    result.en = f"{result.en}\n\n{cta_en}"

        # Add localized hashtags
        cat = category or "motivational"
        result.hashtags_uz = LOCALIZED_HASHTAGS.get("uz", {}).get(cat, [])
        result.hashtags_ru = LOCALIZED_HASHTAGS.get("ru", {}).get(cat, [])
        result.hashtags_en = LOCALIZED_HASHTAGS.get("en", {}).get(cat, [])

        return result

    @classmethod
    def get_profile(cls, lang: str) -> dict:
        return LANGUAGE_PROFILES.get(lang, LANGUAGE_PROFILES["uz"])

    @classmethod
    def _translate_to_ru(cls, uz_text: str, category: str) -> str:
        """Rule-based UZ → RU translation scaffold.

        In production, this would call a translation API.
        For now, wraps the Uzbek text with a Russian context header.
        """
        profile = LANGUAGE_PROFILES["ru"]
        if category == "recipe":
            return f"🍽 {uz_text}\n\n(Узбекская кухня)"
        elif category == "motivational":
            return f"💪 {uz_text}\n\n(Мотивация)"
        elif category == "travel":
            return f"✈️ {uz_text}\n\n(Путешествие по Узбекистану)"
        return f"{uz_text}\n\n{profile['cta_follow']}"

    @classmethod
    def _translate_to_en(cls, uz_text: str, category: str) -> str:
        """Rule-based UZ → EN translation scaffold."""
        profile = LANGUAGE_PROFILES["en"]
        if category == "recipe":
            return f"Traditional Uzbek cuisine\n\n{uz_text}"
        elif category == "motivational":
            return f"Daily motivation from Uzbekistan\n\n{uz_text}"
        elif category == "travel":
            return f"Discover Uzbekistan\n\n{uz_text}"
        return f"{uz_text}\n\n{profile['cta_follow']}"

    @classmethod
    def display(cls) -> str:
        lines = [
            "=" * 60,
            "  Multi-Language Support",
            "=" * 60,
        ]
        for lang, profile in LANGUAGE_PROFILES.items():
            lines.append(f"\n  [{lang}] {profile['name']}")
            lines.append(f"    Greeting: {profile['greeting']}")
            lines.append(f"    CTAs: follow, like, save, comment, share")
            cats = list(LOCALIZED_HASHTAGS.get(lang, {}).keys())
            lines.append(f"    Hashtag pools: {', '.join(cats)}")
        lines.append("=" * 60)
        return "\n".join(lines)
