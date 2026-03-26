"""Screenwriter Agent v2 — AI-powered scripts, captions, voiceover.

Upgraded: Uses Claude claude-sonnet-4-6 for content generation when available.
Falls back to template-based generation when API key is not set.

Best practices (2026):
  - Hook in first 1-2 seconds (question/bold statement)
  - Optimal Reel length: 15-30s for engagement, 60-90s for watch time
  - 3-5 hashtags per post (quality over quantity, 2026 algorithm shift)
  - CTA must feel natural, not forced
  - Uzbek caption with natural Russian/English code-switching
"""

from __future__ import annotations

import random

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

# =====================================================================
# Uzbek hook/CTA templates (fallback when AI not available)
# =====================================================================

HOOK_TEMPLATES = {
    "motivational": [
        "Bugun hayotingizni o'zgartiring!",
        "Siz buni bilasizmi?",
        "Muvaffaqiyatning siri — bu...",
        "90% odamlar buni bilmaydi!",
        "3 soniyada hayotingiz o'zgaradi...",
    ],
    "educational": [
        "Bu 3 ta sir sizga kerak...",
        "Mutaxassislar shuni maslahat beradi...",
        "Ko'pchilik bu xatoni qiladi!",
        "Buni bilmasangiz, kech bo'ladi...",
    ],
    "product": [
        "Buni ko'rib hayron qolasiz!",
        "Sifat va narx — bir joyda!",
        "Eng ko'p sotilgan mahsulot!",
    ],
    "travel": [
        "Bu joyni ko'rganmisiz?",
        "O'zbekistonning eng yashirin joyi!",
        "Bu manzarani ko'ring!",
    ],
    "recipe": [
        "Eng mazali retsept!",
        "Buni sinab ko'ring — pushaymon bo'lmaysiz!",
        "Oilangiz bunga bayram qiladi!",
        "5 daqiqada tayyorlanadi!",
    ],
    "lifestyle": [
        "Sog'lom turmush tarzi sirlari!",
        "Har kuni bu odatni bajaring!",
        "Bugundan boshlang!",
    ],
    "fitness": [
        "10 daqiqada natija ko'ring!",
        "Uy sharoitida mashq!",
        "Tanangizni o'zgartiring!",
    ],
}

CTA_TEMPLATES = {
    "engagement": [
        "Fikringizni kommentda yozing! 👇",
        "Do'stlaringizga ulashing! 📤",
        "Saqlang va keyinroq qarang! 🔖",
        "Like bosing agar foydali bo'lsa! ❤️",
    ],
    "follow": [
        "Obuna bo'ling — ko'proq foydali kontent! 🔔",
        "Follow qiling, yangiliklar o'tkazib yubormang!",
    ],
    "sales": [
        "Hoziroq buyurtma bering! 📩",
        "Bio'dagi linkga o'ting! 🔗",
    ],
}

HASHTAG_POOLS = {
    "motivational": ["motivation", "motivatsiya", "muvaffaqiyat", "mehnat", "success", "mindset", "uzbekistan"],
    "educational": ["education", "talim", "bilim", "tips", "coding", "uzbekdev"],
    "product": ["shopping", "onlineshop", "chegirma", "sale", "madeinuzbekistan"],
    "travel": ["uzbekistan", "travel", "sayohat", "samarkand", "bukhara", "silkroad"],
    "recipe": ["uzbekfood", "retsept", "plov", "taom", "oshpaz", "homecooking"],
    "lifestyle": ["lifestyle", "hayottarzi", "soglomhayot", "wellness", "routine"],
    "fitness": ["fitness", "workout", "sport", "soglomhayot", "mashqlar"],
}


class ScreenwriterAgent(CreativeAgent):
    """Writes scripts, captions, and voiceover — AI-first with rule fallback."""

    role = AgentRole.SCREENWRITER

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info(
            "screenwriter.process",
            topic=brief.topic,
            category=brief.category,
        )

        # Try AI generation first
        ai_result = await self._try_ai_generation(brief)

        if ai_result:
            brief.hook_line = ai_result.get("hook", "")
            brief.cta = ai_result.get("cta", "")
            brief.caption = ai_result.get("full_caption", "")
            brief.hashtags = ai_result.get("hashtags", [])
            brief.voiceover_text = ai_result.get("voiceover_text", "")
            if ai_result.get("script"):
                brief.script = ai_result["script"]
            logger.info("screenwriter.ai_generated")
        else:
            # Fallback to templates
            brief.hook_line = self._generate_hook(brief.category)
            cta_type = "sales" if brief.category == "product" else "engagement"
            brief.cta = self._generate_cta(cta_type)
            brief.hashtags = self._select_hashtags(brief.category)
            if brief.content_type == "reel":
                brief.voiceover_text = self._generate_voiceover(brief)
            brief.caption = self._generate_caption(brief)
            if brief.content_type == "reel":
                brief.script = self._generate_script(brief)
            logger.info("screenwriter.template_generated")

        self.send_message(
            AgentRole.PROMPT_ENGINEER,
            "generate_prompts",
            script=brief.script,
            mood=brief.mood,
        )

        return brief

    async def _try_ai_generation(self, brief: CreativeBrief) -> dict | None:
        """Try generating content with Claude AI."""
        try:
            from skills.ai_content import AIContentGenerator

            gen = AIContentGenerator()
            if not gen.ai_enabled:
                return None

            # Generate caption + hashtags
            caption_result = await gen.generate_caption(
                topic=brief.topic,
                category=brief.category,
                content_type=brief.content_type,
                tone=brief.brand_voice.split(",")[0].strip() if brief.brand_voice else "engaging",
            )

            result = dict(caption_result)

            # Generate script for reels
            if brief.content_type == "reel":
                script_result = await gen.generate_script(
                    topic=brief.topic,
                    category=brief.category,
                    duration=brief.duration,
                    style=brief.style_preset,
                )
                result["voiceover_text"] = script_result.get("voiceover_text", "")
                result["script"] = str(script_result.get("scenes", ""))

            await gen.close()
            return result

        except Exception as exc:
            logger.warning("screenwriter.ai_failed", error=str(exc))
            return None

    def _generate_hook(self, category: str) -> str:
        hooks = HOOK_TEMPLATES.get(category, HOOK_TEMPLATES["motivational"])
        return random.choice(hooks)

    def _generate_cta(self, cta_type: str) -> str:
        ctas = CTA_TEMPLATES.get(cta_type, CTA_TEMPLATES["engagement"])
        return random.choice(ctas)

    def _select_hashtags(self, category: str, count: int = 5) -> list[str]:
        """Select 3-5 hashtags (2026: Instagram caps at 5, quality over quantity)."""
        pool = HASHTAG_POOLS.get(category, [])
        return random.sample(pool, min(count, len(pool)))

    def _generate_voiceover(self, brief: CreativeBrief) -> str:
        parts = [brief.hook_line]
        body_templates = {
            "motivational": f"{brief.topic}. Har bir qadam sizni maqsadingizga yaqinlashtiradi. Ishoning va harakat qiling!",
            "educational": f"Bugun biz {brief.topic} haqida gaplashamiz. Diqqat bilan eshiting — bu juda muhim ma'lumot.",
            "recipe": f"Bugun biz {brief.topic} tayyorlaymiz. Retseptni saqlang va uyda sinab ko'ring!",
            "travel": f"{brief.topic} — bu ajoyib joy. Tarixiy me'morchilik va go'zal manzaralar sizni kutmoqda.",
        }
        body = body_templates.get(brief.category, f"{brief.topic} haqida bilib oling!")
        parts.append(body)
        return " ".join(parts)

    def _generate_caption(self, brief: CreativeBrief) -> str:
        hashtag_str = " ".join(f"#{h}" for h in brief.hashtags[:8])
        return f"{brief.hook_line}\n\n{brief.voiceover_text or brief.topic}\n\n{brief.cta}\n\n—\n{hashtag_str}"

    def _generate_script(self, brief: CreativeBrief) -> str:
        dur = int(brief.duration)
        if dur <= 5:
            return (
                f"[0-1s] HOOK: {brief.hook_line}\n"
                f"[1-3s] MAIN: Visual reveal — {brief.topic}\n"
                f"[3-4s] DETAIL: Close-up / key moment\n"
                f"[4-5s] CTA: {brief.cta}\n"
            )
        return (
            f"[0-2s] HOOK: {brief.hook_line}\n"
            f"[2-4s] ESTABLISH: Wide shot — {brief.topic}\n"
            f"[4-6s] DEVELOP: Detail shots, dynamic movement\n"
            f"[6-8s] CLIMAX: Key reveal / emotional peak\n"
            f"[8-{dur}s] CTA: {brief.cta}\n"
        )
