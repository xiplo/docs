"""Copywriting skills — Uzbek-first Instagram copywriting intelligence."""

from __future__ import annotations

import random


class CopywritingSkills:
    """Skills for writing engaging Uzbek Instagram copy."""

    # Uzbek emotional trigger words
    EMOTIONAL_TRIGGERS = {
        "curiosity": ["bilasizmi", "sir", "kashf eting", "hech kim bilmaydi"],
        "urgency": ["hoziroq", "bugun", "faqat", "oxirgi imkoniyat"],
        "belonging": ["biz bilan", "hamjamiyat", "birga", "oila"],
        "aspiration": ["muvaffaqiyat", "orzu", "maqsad", "kelajak"],
        "fear_of_missing": ["o'tkazib yubormang", "chegirma tugaydi", "qolmang"],
    }

    # Caption formulas
    CAPTION_FORMULAS = {
        "AIDA": {
            "structure": "Attention → Interest → Desire → Action",
            "template": "{attention}\n\n{interest}\n\n{desire}\n\n{action}",
        },
        "PAS": {
            "structure": "Problem → Agitate → Solution",
            "template": "{problem}\n\n{agitate}\n\n{solution}",
        },
        "BAB": {
            "structure": "Before → After → Bridge",
            "template": "{before}\n\n{after}\n\n{bridge}",
        },
        "HOOK_STORY_CTA": {
            "structure": "Hook → Story → Call-to-Action",
            "template": "{hook}\n\n{story}\n\n{cta}",
        },
    }

    @classmethod
    def write_hook(cls, category: str, style: str = "question") -> str:
        """Generate a scroll-stopping hook line in Uzbek."""
        hooks = {
            "question": {
                "motivational": "Nima uchun 90% odamlar maqsadiga erishmaydi?",
                "educational": "Bu sir sizning hayotingizni o'zgartiradi!",
                "product": "Nima uchun hammaning sevimli mahsuloti?",
                "recipe": "Eng mazali retseptni bilasizmi?",
                "travel": "Bu joyni hali ko'rmaganmisiz?",
                "fashion": "Bu uslub hamma joyda trend bo'ldi!",
                "tech": "Bu texnologiyani sinab ko'rdingizmi?",
            },
            "statement": {
                "motivational": "Bugun siz hayotingizni o'zgartirasiz.",
                "educational": "Buni bilgan odam doim yutuqda.",
                "product": "Sifatni tushunganlar buni tanlaydi.",
                "recipe": "Buni tatib ko'rganlar boshqasini xohlamaydi.",
                "travel": "Bu joy sizni lol qoldiradi.",
                "fashion": "Moda — bu o'zingizni ifoda etish.",
                "tech": "Kelajak bugun boshlanadi.",
            },
            "number": {
                "motivational": "Muvaffaqiyatning 5 ta qoidasi!",
                "educational": "3 ta sir — buni hamma bilishi kerak!",
                "product": "7 ta sabab nega bu mahsulot eng yaxshi!",
                "recipe": "5 daqiqada tayyorlanadigan 3 ta retsept!",
                "travel": "O'zbekistonning 10 ta eng go'zal joyi!",
                "fashion": "2024 yilning 5 ta asosiy trendi!",
                "tech": "Har bir dasturchi bilishi kerak bo'lgan 7 ta tool!",
            },
        }
        style_hooks = hooks.get(style, hooks["question"])
        return style_hooks.get(category, "Bugun yangi narsa o'rganing!")

    @classmethod
    def write_caption_by_formula(
        cls,
        formula: str,
        components: dict[str, str],
    ) -> str:
        """Write a caption using a specific copywriting formula."""
        f = cls.CAPTION_FORMULAS.get(formula, cls.CAPTION_FORMULAS["HOOK_STORY_CTA"])
        return f["template"].format(**components)

    @classmethod
    def add_emotional_triggers(
        cls, text: str, emotions: list[str] | None = None
    ) -> str:
        """Enhance text with emotional trigger words."""
        if not emotions:
            emotions = ["curiosity", "aspiration"]

        triggers = []
        for emotion in emotions:
            words = cls.EMOTIONAL_TRIGGERS.get(emotion, [])
            if words:
                triggers.append(random.choice(words))

        if triggers:
            return f"{text} — {' '.join(triggers)}!"
        return text

    @staticmethod
    def format_hashtags(tags: list[str], max_count: int = 20) -> str:
        """Format hashtags for Instagram with optimal count."""
        unique = list(dict.fromkeys(tags))[:max_count]
        return " ".join(f"#{tag.strip('#')}" for tag in unique)

    @staticmethod
    def write_bio_cta(action: str, benefit: str) -> str:
        """Write a bio-friendly CTA."""
        return f"👉 {action} — {benefit}"

    @staticmethod
    def estimate_reading_time(text: str) -> float:
        """Estimate reading time in seconds (avg 150 words/min for Uzbek)."""
        words = len(text.split())
        return (words / 150) * 60

    @classmethod
    def optimize_for_voiceover(cls, text: str, max_seconds: float) -> str:
        """Trim/optimize text to fit within a voiceover duration."""
        reading_time = cls.estimate_reading_time(text)
        if reading_time <= max_seconds:
            return text

        # Truncate to fit
        words = text.split()
        target_words = int((max_seconds / 60) * 150)
        if target_words < len(words):
            return " ".join(words[:target_words]) + "..."
        return text
