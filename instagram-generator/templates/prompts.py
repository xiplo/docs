"""Content templates and prompt library for Uzbek Instagram content.

Each template defines:
  - image_prompt: what to generate visually (Nano Banana)
  - voiceover_text: Uzbek script for Eleven Labs TTS
  - caption: Instagram caption with Uzbek + English
  - hashtags: relevant hashtags
  - subtitle_text: on-screen text overlay
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Category = Literal[
    "motivational",
    "educational",
    "product",
    "lifestyle",
    "recipe",
    "travel",
    "tech",
    "fashion",
    "humor",
]


@dataclass
class ContentTemplate:
    name: str
    category: Category
    content_type: str  # reel, image, carousel, story
    image_prompt: str
    caption: str
    voiceover_text: str = ""
    subtitle_text: str = ""
    carousel_prompts: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    image_style: str = "photorealistic"
    video_duration: str = "5"


# =====================================================================
# Template library
# =====================================================================

TEMPLATES: list[ContentTemplate] = [
    # -----------------------------------------------------------------
    # Motivational Reels
    # -----------------------------------------------------------------
    ContentTemplate(
        name="morning_motivation",
        category="motivational",
        content_type="reel",
        image_prompt=(
            "Cinematic sunrise over Samarkand Registan square, golden hour light, "
            "dramatic clouds, ultra detailed, 8k photography, warm tones, "
            "silhouette of a person standing in awe"
        ),
        voiceover_text=(
            "Har bir kun — yangi imkoniyat. Bugun siz uchun eng yaxshi kun bo'lsin. "
            "Maqsadlaringizga qadam qo'ying va hech qachon to'xtamang!"
        ),
        caption=(
            "Har bir tong — yangi boshlanish! ☀️\n"
            "Bugun o'zingizning eng yaxshi versiyangiz bo'ling."
        ),
        subtitle_text="Har bir kun — yangi imkoniyat!",
        hashtags=[
            "motivation", "uzbekistan", "samarkand", "morningvibes",
            "hustle", "mindset", "uzbek", "motivatsiya",
        ],
        video_duration="5",
    ),

    ContentTemplate(
        name="success_mindset",
        category="motivational",
        content_type="reel",
        image_prompt=(
            "Powerful businessman standing on top of a modern skyscraper at night, "
            "city lights below, cinematic lighting, dramatic angle, "
            "suit and tie, confident pose, ultra realistic"
        ),
        voiceover_text=(
            "Muvaffaqiyat — bu tasodif emas. Bu har kuni qilingan kichik qarorlar "
            "natijasi. Bugun nima qilasiz? O'zingizni rivojlantiring!"
        ),
        caption=(
            "Muvaffaqiyat yo'li qiyinchiliklardan o'tadi 💪\n"
            "Lekin natija bunga arziydi!"
        ),
        subtitle_text="Muvaffaqiyat — bu har kungi tanlov!",
        hashtags=[
            "success", "mindset", "entrepreneur", "uzbek",
            "businessman", "motivation", "tashkent",
        ],
        video_duration="5",
    ),

    # -----------------------------------------------------------------
    # Educational content
    # -----------------------------------------------------------------
    ContentTemplate(
        name="tech_tips",
        category="educational",
        content_type="carousel",
        image_prompt="Modern tech workspace with multiple monitors showing code",
        carousel_prompts=[
            "Clean minimalist slide with title 'Dasturlashni o'rganing' on dark blue gradient background, modern typography, tech icons",
            "Infographic slide showing Python programming language benefits, modern flat design, dark theme with neon accents",
            "Step by step guide slide showing laptop with code editor, numbered steps 1-2-3, clean dark design",
            "Final slide with call to action 'Boshlang!' on gradient purple-blue background, modern design",
        ],
        caption=(
            "Dasturlashni o'rganish uchun 4 ta muhim qadam 💻\n\n"
            "1️⃣ Tilni tanlang (Python tavsiya etiladi)\n"
            "2️⃣ Har kuni 1 soat mashq qiling\n"
            "3️⃣ Loyihalar yarating\n"
            "4️⃣ Jamiyatga qo'shiling\n\n"
            "Saqlang va do'stlaringiz bilan ulashing! 🔖"
        ),
        hashtags=[
            "coding", "python", "uzbekdev", "programming",
            "tech", "education", "dasturlash",
        ],
        image_style="flat_design",
    ),

    # -----------------------------------------------------------------
    # Product showcase
    # -----------------------------------------------------------------
    ContentTemplate(
        name="product_launch",
        category="product",
        content_type="reel",
        image_prompt=(
            "Luxury product photography on marble surface, soft studio lighting, "
            "bokeh background, premium feel, golden accents, ultra detailed"
        ),
        voiceover_text=(
            "Yangi mahsulotimiz bilan tanishing! Sifat va zamonaviy dizayn — "
            "barchasi siz uchun yaratilgan. Hoziroq buyurtma bering!"
        ),
        caption=(
            "🆕 Yangi kolleksiya sizni kutmoqda!\n"
            "Sifat. Dizayn. Narx. — Hammasi bir joyda.\n\n"
            "📩 DM orqali buyurtma bering"
        ),
        subtitle_text="Yangi kolleksiya!",
        hashtags=[
            "newproduct", "uzbekistan", "shopping", "onlineshop",
            "tashkent", "quality", "yangi",
        ],
        video_duration="5",
    ),

    # -----------------------------------------------------------------
    # Travel / Lifestyle
    # -----------------------------------------------------------------
    ContentTemplate(
        name="uzbekistan_travel",
        category="travel",
        content_type="reel",
        image_prompt=(
            "Breathtaking aerial view of Khiva old city at sunset, "
            "ancient Islamic architecture, warm golden light, "
            "cinematic drone shot, ultra wide angle, 8k"
        ),
        voiceover_text=(
            "O'zbekistonning go'zalligini kashf eting! Xiva — ming yillik tarix, "
            "ajoyib me'morchilik va unutilmas taassurotlar shahri."
        ),
        caption=(
            "🏛 Xiva — vaqt to'xtagan shahar\n"
            "Ming yillik tarix, ajoyib me'morchilik ✨\n\n"
            "O'zbekistonga tashrif buyuring!"
        ),
        subtitle_text="Xiva — vaqt to'xtagan shahar",
        hashtags=[
            "uzbekistan", "khiva", "travel", "centralasia",
            "heritage", "tourism", "sayohat", "xiva",
        ],
        video_duration="10",
    ),

    # -----------------------------------------------------------------
    # Recipe / Food
    # -----------------------------------------------------------------
    ContentTemplate(
        name="uzbek_plov",
        category="recipe",
        content_type="reel",
        image_prompt=(
            "Traditional Uzbek plov in a large cast iron kazan, "
            "steam rising, garnished with quail eggs and raisins, "
            "overhead shot, rustic wooden table, warm lighting, food photography"
        ),
        voiceover_text=(
            "Haqiqiy o'zbek palovi tayyorlash sirlarini bilib oling! "
            "Eng asosiysi — sabr va yaxshi guruch. "
            "Retseptni saqlang va sinab ko'ring!"
        ),
        caption=(
            "🍚 Haqiqiy O'zbek Palovi\n\n"
            "Masalliqlar:\n"
            "• 1 kg guruch\n"
            "• 500g go'sht\n"
            "• 500g sabzi\n"
            "• 300g piyoz\n"
            "• Ziravorlar\n\n"
            "To'liq retseptni saqlang! 📌"
        ),
        subtitle_text="O'zbek palovi tayyorlash sirlari",
        hashtags=[
            "plov", "uzbekfood", "recipe", "cooking",
            "oshpaz", "uzbekcuisine", "palov", "taom",
        ],
        video_duration="10",
    ),

    # -----------------------------------------------------------------
    # Fashion
    # -----------------------------------------------------------------
    ContentTemplate(
        name="fashion_lookbook",
        category="fashion",
        content_type="carousel",
        image_prompt="Fashion model in modern Uzbek-inspired outfit, studio shot",
        carousel_prompts=[
            "Fashion model wearing modern interpretation of Uzbek atlas fabric dress, studio lighting, editorial photography, clean white background",
            "Close-up detail shot of intricate ikat pattern on silk fabric, macro photography, vibrant colors",
            "Full body shot of model in contemporary Uzbek-fusion streetwear, urban background, golden hour",
            "Accessories flat lay with traditional Uzbek jewelry modernized, marble surface, top-down shot",
        ],
        caption=(
            "🇺🇿 Zamonaviy O'zbek modasi\n\n"
            "An'anaviy naqshlar + zamonaviy uslub = ajoyib kombinatsiya ✨\n\n"
            "Qaysi look yoqdi? Kommentda yozing! 👇"
        ),
        hashtags=[
            "uzbekfashion", "atlas", "ikat", "fashion",
            "style", "ootd", "tashkentfashion", "moda",
        ],
        image_style="photorealistic",
    ),

    # -----------------------------------------------------------------
    # Story template
    # -----------------------------------------------------------------
    ContentTemplate(
        name="daily_quote_story",
        category="motivational",
        content_type="story",
        image_prompt=(
            "Elegant minimal quote background, soft gradient from deep purple to "
            "midnight blue, subtle light particles, space for text overlay, "
            "vertical 9:16 format, dreamy atmosphere"
        ),
        caption="",
        subtitle_text="",
        hashtags=[],
        image_style="illustration",
    ),
]


def get_templates_by_category(category: Category) -> list[ContentTemplate]:
    return [t for t in TEMPLATES if t.category == category]


def get_template_by_name(name: str) -> ContentTemplate | None:
    for t in TEMPLATES:
        if t.name == name:
            return t
    return None


def list_template_names() -> list[str]:
    return [t.name for t in TEMPLATES]
