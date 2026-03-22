"""Screenwriter Agent (Сценарист) — writes scripts, captions, voiceover texts.

The Screenwriter:
  - Creates compelling scripts for video content (Reels)
  - Writes Instagram captions optimized for engagement
  - Generates voiceover text in Uzbek language
  - Crafts hook lines (first 3 seconds attention grabber)
  - Writes CTAs (Call-to-Action)
  - Selects relevant hashtags
"""

from __future__ import annotations

import random

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

# =====================================================================
# Uzbek script templates and building blocks
# =====================================================================

HOOK_TEMPLATES = {
    "motivational": [
        "Bugun hayotingizni o'zgartiring!",
        "Siz buni bilasizmi?",
        "Muvaffaqiyatning siri — bu...",
        "Har kuni bu oddiy odatni bajaring...",
        "90% odamlar buni bilmaydi!",
    ],
    "educational": [
        "Bugun siz yangi narsa o'rganasiz!",
        "Bu 3 ta sir sizga kerak...",
        "Mutaxassislar shuni maslahat beradi...",
        "Eng muhim qoida — bu...",
        "Ko'pchilik bu xatoni qiladi!",
    ],
    "product": [
        "Yangi mahsulot sizni kutmoqda!",
        "Sifat va narx — bir joyda!",
        "Buni ko'rib hayron qolasiz!",
        "Chegirma faqat bugun!",
        "Eng ko'p sotilgan mahsulot!",
    ],
    "travel": [
        "Bu joyni ko'rganmisiz?",
        "O'zbekistonning ajoyib joylari!",
        "Bu manzarani ko'ring!",
        "Sayohatga tayyormisiz?",
        "Eng go'zal joy — bu...",
    ],
    "recipe": [
        "Eng mazali retsept!",
        "Buni sinab ko'ring — pushaymon bo'lmaysiz!",
        "Oson va tez tayyorlanadi!",
        "Oilangiz bunga bayram qiladi!",
        "Sir retsept ochiladi!",
    ],
    "fashion": [
        "Bu uslub sizga mos keladi!",
        "2024 yilning eng trendy ko'rinishi!",
        "Shunchaki chiroyli!",
        "Bu kombinatsiyani sinab ko'ring!",
        "Moda dunyosidan yangilik!",
    ],
    "tech": [
        "Bu texnologiya hayotingizni osonlashtiradi!",
        "Yangi funksiya — sinab ko'ring!",
        "Buni bilish sizga kerak!",
        "Texnologiya yangiliklari!",
        "Har bir dasturchi bilishi kerak!",
    ],
    "lifestyle": [
        "Sog'lom turmush tarzi sirlari!",
        "Har kuni bu odatni bajaring!",
        "Hayot sifatingizni oshiring!",
        "Oddiy qadamlar — katta natijalar!",
        "Bugundan boshlang!",
    ],
    "humor": [
        "Kulib yuboring! 😂",
        "Bu tanish vaziyat!",
        "Hammaga bo'lgan!",
        "Javob kommentlarda! 😄",
        "Kim o'zini tanidi?",
    ],
}

CTA_TEMPLATES = {
    "engagement": [
        "Fikringizni kommentda yozing! 👇",
        "Do'stlaringizga ulashing! 📤",
        "Saqlang va keyinroq o'qing! 🔖",
        "Like bosing agar foydali bo'lsa! ❤️",
        "Qaysi biri yoqdi? Yozing! 💬",
    ],
    "sales": [
        "Hoziroq buyurtma bering! 📩",
        "DM yozing — batafsil ma'lumot beramiz!",
        "Bio'dagi linkga o'ting! 🔗",
        "Chegirma kodi: INSTAGRAM20 🎁",
        "O'lchov va ranglarni DM'da so'rang!",
    ],
    "follow": [
        "Obuna bo'ling — ko'proq foydali kontent! 🔔",
        "Follow qiling, yangiliklar o'tkazib yubormang!",
        "Biz bilan birga o'sib boring! 📈",
    ],
}

HASHTAG_POOLS = {
    "motivational": [
        "motivation", "motivatsiya", "uzbek", "success", "muvaffaqiyat",
        "hustle", "mindset", "tafakkur", "o'zbekiston", "tashkent",
        "inspiringquotes", "ilhom", "hayot", "maqsad", "kuch",
    ],
    "educational": [
        "education", "ta'lim", "o'rganish", "tips", "maslahat",
        "bilim", "fan", "texnologiya", "dasturlash", "coding",
    ],
    "product": [
        "newproduct", "shopping", "onlineshop", "tashkentshopping",
        "sifat", "yangi", "chegirma", "sale", "madeinuzbekistan",
    ],
    "travel": [
        "uzbekistan", "travel", "sayohat", "samarkand", "bukhara",
        "khiva", "tashkent", "centralasia", "tourism", "heritage",
    ],
    "recipe": [
        "uzbekfood", "recipe", "retsept", "plov", "oshpaz",
        "cooking", "taom", "milliyovqat", "foodie", "homecooking",
    ],
    "fashion": [
        "fashion", "moda", "style", "uslub", "ootd",
        "uzbekfashion", "atlas", "adras", "trend", "lookbook",
    ],
    "tech": [
        "tech", "technology", "coding", "dasturlash", "uzbekdev",
        "programming", "startup", "innovation", "ai", "digital",
    ],
    "lifestyle": [
        "lifestyle", "hayottarzi", "healthy", "sog'lom", "wellness",
        "selfcare", "positivevibes", "routine", "habits", "growth",
    ],
    "humor": [
        "humor", "kulgili", "funny", "meme", "uzbekhumor",
        "comedy", "kulgu", "fun", "relatable", "lol",
    ],
}

# Caption structure templates
CAPTION_STRUCTURES = {
    "reel": {
        "motivational": (
            "{hook}\n\n"
            "{body}\n\n"
            "{cta}\n\n"
            "—\n{hashtags}"
        ),
        "educational": (
            "{hook}\n\n"
            "{body}\n\n"
            "💡 Saqlang va do'stlaringizga ulashing!\n\n"
            "{cta}\n\n"
            "—\n{hashtags}"
        ),
        "default": (
            "{hook}\n\n"
            "{body}\n\n"
            "{cta}\n\n"
            "—\n{hashtags}"
        ),
    },
    "carousel": {
        "default": (
            "{hook}\n\n"
            "{body}\n\n"
            "➡️ Chapga surting ko'proq o'qish uchun!\n\n"
            "{cta}\n\n"
            "—\n{hashtags}"
        ),
    },
    "image": {
        "default": "{hook}\n\n{body}\n\n{cta}\n\n—\n{hashtags}",
    },
    "story": {
        "default": "",
    },
}


class ScreenwriterAgent(CreativeAgent):
    """Writes scripts, captions, and voiceover for Uzbek Instagram content."""

    role = AgentRole.SCREENWRITER

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info(
            "screenwriter.process",
            topic=brief.topic,
            category=brief.category,
            content_type=brief.content_type,
        )

        # 1. Generate hook line
        brief.hook_line = self._generate_hook(brief.category)

        # 2. Generate CTA
        cta_type = "sales" if brief.category == "product" else "engagement"
        brief.cta = self._generate_cta(cta_type)

        # 3. Generate hashtags
        brief.hashtags = self._select_hashtags(brief.category)

        # 4. Generate voiceover script (for reels)
        if brief.content_type == "reel":
            brief.voiceover_text = self._generate_voiceover(brief)

        # 5. Generate caption
        brief.caption = self._generate_caption(brief)

        # 6. Generate script outline (scene descriptions)
        if brief.content_type == "reel":
            brief.script = self._generate_script(brief)

        self.send_message(
            AgentRole.PROMPT_ENGINEER,
            "generate_prompts",
            script=brief.script,
            mood=brief.mood,
        )

        return brief

    def _generate_hook(self, category: str) -> str:
        hooks = HOOK_TEMPLATES.get(category, HOOK_TEMPLATES["motivational"])
        return random.choice(hooks)

    def _generate_cta(self, cta_type: str) -> str:
        ctas = CTA_TEMPLATES.get(cta_type, CTA_TEMPLATES["engagement"])
        return random.choice(ctas)

    def _select_hashtags(self, category: str, count: int = 15) -> list[str]:
        pool = HASHTAG_POOLS.get(category, [])
        # Mix category-specific + general
        general = ["instagram", "viral", "trending", "explore", "fyp"]
        combined = pool + general
        selected = random.sample(combined, min(count, len(combined)))
        return selected

    def _generate_voiceover(self, brief: CreativeBrief) -> str:
        """Generate a voiceover script based on topic and category."""
        # Structure: Hook → Body → CTA
        parts = [brief.hook_line]

        # Body — varies by category
        body_templates = {
            "motivational": (
                f"{brief.topic}. "
                "Har bir qadam sizni maqsadingizga yaqinlashtiradi. "
                "Ishoning va harakat qiling!"
            ),
            "educational": (
                f"Bugun biz {brief.topic} haqida gaplashamiz. "
                "Diqqat bilan eshiting — bu juda muhim ma'lumot."
            ),
            "product": (
                f"Yangi {brief.topic} sizni kutmoqda! "
                "Sifat, dizayn va arzon narx — barchasi bir joyda."
            ),
            "travel": (
                f"{brief.topic} — bu ajoyib joy. "
                "Tarixiy me'morchilik va go'zal manzaralar sizni kutmoqda."
            ),
            "recipe": (
                f"Bugun biz {brief.topic} tayyorlaymiz. "
                "Retseptni saqlang va uyda sinab ko'ring!"
            ),
        }
        body = body_templates.get(
            brief.category,
            f"{brief.topic} haqida bilib oling!",
        )
        parts.append(body)

        return " ".join(parts)

    def _generate_caption(self, brief: CreativeBrief) -> str:
        """Assemble the final caption from components."""
        structure = (
            CAPTION_STRUCTURES
            .get(brief.content_type, {})
            .get(brief.category, CAPTION_STRUCTURES.get(brief.content_type, {}).get("default", "{body}"))
        )

        hashtag_str = " ".join(f"#{h}" for h in brief.hashtags)

        return structure.format(
            hook=brief.hook_line,
            body=brief.voiceover_text or brief.topic,
            cta=brief.cta,
            hashtags=hashtag_str,
        )

    def _generate_script(self, brief: CreativeBrief) -> str:
        """Generate a scene-by-scene script outline."""
        if brief.duration == "5":
            return (
                f"[0-1s] HOOK: {brief.hook_line}\n"
                f"[1-3s] MAIN: Visual reveal — {brief.topic}\n"
                f"[3-4s] DETAIL: Close-up / key moment\n"
                f"[4-5s] CTA: {brief.cta}\n"
            )
        else:  # 10s
            return (
                f"[0-2s] HOOK: {brief.hook_line}\n"
                f"[2-4s] ESTABLISH: Wide shot — {brief.topic}\n"
                f"[4-6s] DEVELOP: Detail shots, dynamic movement\n"
                f"[6-8s] CLIMAX: Key reveal / emotional peak\n"
                f"[8-10s] CTA: {brief.cta}\n"
            )
