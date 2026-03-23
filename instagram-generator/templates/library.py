"""Pre-built content templates — ready-to-use content blueprints.

Each template defines:
  - topic, category, content_type
  - caption template (with {placeholders})
  - hashtag set
  - style preset, duration
  - voiceover text template

Use these as starting points or auto-generate from them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ContentTemplate:
    """A reusable content blueprint."""

    name: str
    topic: str
    category: str
    content_type: str = "reel"
    caption_template: str = ""
    hashtags: list[str] = field(default_factory=list)
    voiceover_template: str = ""
    style_preset: str = "photorealistic"
    duration: str = "5"
    image_prompt_template: str = ""

    def render(self, **kwargs) -> dict:
        """Render template with provided variables."""
        return {
            "topic": self.topic.format(**kwargs) if kwargs else self.topic,
            "category": self.category,
            "content_type": self.content_type,
            "caption": self.caption_template.format(**kwargs) if kwargs else self.caption_template,
            "hashtags": self.hashtags,
            "voiceover_text": self.voiceover_template.format(**kwargs) if kwargs else self.voiceover_template,
            "style_preset": self.style_preset,
            "duration": self.duration,
            "image_prompt": self.image_prompt_template.format(**kwargs) if kwargs else self.image_prompt_template,
        }


# =====================================================================
# Pre-built template library
# =====================================================================

TEMPLATE_LIBRARY: list[ContentTemplate] = [
    # --- Motivational ---
    ContentTemplate(
        name="morning_motivation",
        topic="Ertalabki motivatsiya — yangi kunga kuch",
        category="motivational",
        content_type="reel",
        caption_template="Har bir yangi kun — yangi imkoniyat!\n\nBugun nima qilasiz?",
        hashtags=["motivation", "uzbekmotivation", "muvaffaqiyat", "ertalab", "yangiKun"],
        voiceover_template="Har bir tong sizga yangi imkoniyat beradi. Bugun o'z maqsadingizga bir qadam yaqinlashing.",
        style_preset="cinematic",
        duration="7",
        image_prompt_template="Golden sunrise over Tashkent city skyline, warm light, motivational atmosphere, cinematic",
    ),
    ContentTemplate(
        name="success_story",
        topic="Muvaffaqiyat sirri — mehnat va sabr",
        category="motivational",
        content_type="reel",
        caption_template="Muvaffaqiyatga olib boradigan yo'l — mehnat va sabr.\n\nSiz ham bugundan boshlang!",
        hashtags=["success", "biznes", "mehnat", "sabr", "tadbirkorlik"],
        voiceover_template="Muvaffaqiyat bir kunda kelmaydi. Lekin har kuni qilingan kichik qadam katta natijaga olib boradi.",
        style_preset="cinematic",
        duration="8",
        image_prompt_template="Young entrepreneur working in modern office in Tashkent, determined expression, warm lighting",
    ),
    ContentTemplate(
        name="daily_quote",
        topic="Kunlik iqtibos",
        category="motivational",
        content_type="image",
        caption_template="Bugungi fikr: Eng katta sarmoya — bu o'zingizga sarmoya.",
        hashtags=["quote", "motivatsiya", "iqtibos", "bilim", "hayot"],
        style_preset="artistic",
        image_prompt_template="Elegant typography on dark background, motivational quote design, minimal, professional",
    ),

    # --- Recipe ---
    ContentTemplate(
        name="palov_recipe",
        topic="An'anaviy o'zbek palovi",
        category="recipe",
        content_type="reel",
        caption_template="Palov — o'zbek dastxonining shoh taomi!\n\nRetseptni saqlang!",
        hashtags=["palov", "uzbekfood", "taom", "retsept", "oshpaz", "dastxon"],
        voiceover_template="Hozir biz an'anaviy o'zbek palovini tayyorlaymiz. Buning uchun guruch, sabzi, go'sht va ziravorlar kerak.",
        style_preset="photorealistic",
        duration="12",
        image_prompt_template="Traditional Uzbek plov in a large kazan, steam rising, colorful carrots, photorealistic food photography",
    ),
    ContentTemplate(
        name="somsa_recipe",
        topic="Uy sharoitida somsa tayyorlash",
        category="recipe",
        content_type="reel",
        caption_template="Uy somsasi — issiq va mazali!\n\nQadamma-qadam retsept.",
        hashtags=["somsa", "uzbekfood", "taom", "pechenye", "oshxona"],
        voiceover_template="Bugun biz uy sharoitida somsa tayyorlaymiz. Xamir va go'shtli ichlikni tayyorlashdan boshlaymiz.",
        style_preset="photorealistic",
        duration="10",
        image_prompt_template="Fresh golden samsa pastries on a plate, flaky layers, steam, Uzbek kitchen background",
    ),

    # --- Travel ---
    ContentTemplate(
        name="registon_tour",
        topic="Registon maydoni — Samarqand durdonasi",
        category="travel",
        content_type="reel",
        caption_template="Registon — dunyoning eng go'zal maydonlaridan biri.\n\nSamarqandga tashrif buyuring!",
        hashtags=["registon", "samarkand", "uzbekistan", "silkroad", "travel", "heritage"],
        voiceover_template="Registon maydoni — Samarqandning yuragi. Uch ulkan madrasa qadimiy me'morchilik san'atining ajoyib namunasidir.",
        style_preset="cinematic",
        duration="10",
        image_prompt_template="Registan Square in Samarkand at golden hour, three madrasas, blue tiles, cinematic wide shot",
    ),
    ContentTemplate(
        name="tashkent_modern",
        topic="Zamonaviy Toshkent",
        category="travel",
        content_type="reel",
        caption_template="Toshkent — Sharq va G'arb uyg'unligi.\n\nQaysi joyni yaxshi ko'rasiz?",
        hashtags=["tashkent", "toshkent", "uzbekistan", "citylife", "modern"],
        voiceover_template="Toshkent — zamonaviy binolar va tarixiy obidalar uyg'unlashgan shahar. Keling, birga sayohat qilamiz.",
        style_preset="cinematic",
        duration="8",
        image_prompt_template="Modern Tashkent cityscape, Tashkent City Park, glass buildings alongside traditional architecture, sunset",
    ),

    # --- Lifestyle ---
    ContentTemplate(
        name="morning_routine",
        topic="Ertalabki tartib — samarali kun",
        category="lifestyle",
        content_type="reel",
        caption_template="Mening ertalabki tartibim:\n1. Suv ichish\n2. Sport\n3. Kitob o'qish\n4. Ish boshlanadi!",
        hashtags=["morningroutine", "lifestyle", "ertalab", "tartib", "soglomhayot"],
        voiceover_template="Samarali kun ertalabdan boshlanadi. Keling, kunni to'g'ri rejalashtirish usullarini ko'rib chiqamiz.",
        style_preset="photorealistic",
        duration="7",
        image_prompt_template="Young person doing morning routine, bright natural light, clean modern apartment, lifestyle photography",
    ),

    # --- Education ---
    ContentTemplate(
        name="uzbek_language_tip",
        topic="O'zbek tili — kundalik foydali so'zlar",
        category="education",
        content_type="image",
        caption_template="Bugun yangi so'z o'rganamiz!\n\nSaqlang va do'stlaringiz bilan ulashing.",
        hashtags=["uzbektili", "tilorganish", "bilim", "talim", "lugat"],
        style_preset="artistic",
        image_prompt_template="Clean educational infographic design, Uzbek language vocabulary, modern typography, gradient background",
    ),

    # --- Fitness ---
    ContentTemplate(
        name="home_workout",
        topic="Uy sharoitida mashqlar",
        category="fitness",
        content_type="reel",
        caption_template="Trenajyorzalga bormasdan ham sport qilish mumkin!\n\n5 oddiy mashq.",
        hashtags=["workout", "fitness", "uydamashq", "sport", "soglomhayot"],
        voiceover_template="Uy sharoitida 10 daqiqali mashqlar bilan tanangizni mustahkamlang. Hech qanday jihozlar shart emas.",
        style_preset="photorealistic",
        duration="8",
        image_prompt_template="Person doing bodyweight exercises at home, bright room, workout mat, energetic mood",
    ),
]


class TemplateLibrary:
    """Manage and browse content templates."""

    @classmethod
    def get_all(cls) -> list[ContentTemplate]:
        return TEMPLATE_LIBRARY

    @classmethod
    def get_by_category(cls, category: str) -> list[ContentTemplate]:
        return [t for t in TEMPLATE_LIBRARY if t.category == category]

    @classmethod
    def get_by_name(cls, name: str) -> ContentTemplate | None:
        for t in TEMPLATE_LIBRARY:
            if t.name == name:
                return t
        return None

    @classmethod
    def get_by_type(cls, content_type: str) -> list[ContentTemplate]:
        return [t for t in TEMPLATE_LIBRARY if t.content_type == content_type]

    @classmethod
    def display(cls, category: str = "") -> str:
        templates = cls.get_by_category(category) if category else cls.get_all()

        lines = [
            "=" * 65,
            "  Content Template Library",
            "=" * 65,
        ]

        by_cat: dict[str, list[ContentTemplate]] = {}
        for t in templates:
            by_cat.setdefault(t.category, []).append(t)

        for cat, tmpls in by_cat.items():
            lines.append(f"\n  {cat.upper()} ({len(tmpls)} templates)")
            for t in tmpls:
                tags = len(t.hashtags)
                lines.append(
                    f"    {t.name:<22} {t.content_type:<7} "
                    f"{tags} tags  {t.topic[:35]}"
                )

        lines.append(f"\n  Total: {len(templates)} templates")
        lines.append("=" * 65)
        return "\n".join(lines)
