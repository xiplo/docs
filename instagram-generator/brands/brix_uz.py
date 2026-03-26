"""BRIX.UZ brand profile — industrial equipment supplier in Uzbekistan.

Company: BRIX.UZ
Industry: Industrial equipment, material handling, engineering services
Products: Forklifts, stackers, cranes, hoists, conveyors, labeling equipment
Location: Tashkent, Uzbekistan (delivery nationwide)
Target: B2B (factories, warehouses, logistics) + B2C awareness
Languages: Uzbek (primary), Russian (B2B), English (international)

Social strategy: Behind-the-scenes, equipment demos, satisfying machinery,
educational industrial content — viral on TikTok/Reels in 2026.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BrixBrandProfile:
    """BRIX.UZ brand configuration."""

    name: str = "BRIX.UZ"
    tagline_uz: str = "Sanoat uskunalari — ishonchli yechimlar"
    tagline_ru: str = "Промышленное оборудование — надёжные решения"
    tagline_en: str = "Industrial Equipment — Reliable Solutions"

    brand_voice: str = "professional, reliable, modern, powerful"
    tone: str = "confident, educational, slightly awe-inspiring"
    target_audience: str = "B2B: factory managers, warehouse ops, logistics directors in Uzbekistan. B2C: viral industrial content fans 18-35"

    colors: list[str] = field(default_factory=lambda: [
        "#1E3A5F",  # Dark blue (trust, industry)
        "#FF6B00",  # Orange (energy, action)
        "#FFFFFF",  # White (clean, modern)
        "#2D2D2D",  # Dark gray (machinery)
    ])

    categories: list[str] = field(default_factory=lambda: [
        "equipment_demo",
        "behind_the_scenes",
        "satisfying_machinery",
        "educational",
        "before_after",
        "warehouse_transformation",
        "safety_tips",
        "client_stories",
    ])

    products: list[str] = field(default_factory=lambda: [
        "Vilkali yuklagich (forklift)",
        "Elektr stacker",
        "Ko'prikli kran (overhead crane)",
        "Portal kran (gantry crane)",
        "Konveyer liniyasi",
        "Palet aravachasi (rokhla)",
        "Yuk ko'tarish jihozlari (hoist)",
        "Etiketlash uskunasi",
        "Mezzanin javonlar",
        "Akkumulyator zaryadlovchi",
    ])

    hashtags: list[str] = field(default_factory=lambda: [
        "brixuz", "sanoatuskunalari", "forklift", "warehouse",
        "madeinuzbekistan",
    ])

    platforms: list[str] = field(default_factory=lambda: [
        "instagram", "tiktok", "telegram", "youtube", "facebook",
    ])


# =====================================================================
# Viral content briefs for BRIX.UZ — Uzbek industrial market
# =====================================================================

VIRAL_CONTENT_BRIEFS = [
    # --- SATISFYING MACHINERY (highest viral potential) ---
    {
        "id": "brix_01_forklift_dance",
        "topic": "Forklift harakati — bir harakat, 2 tonna yuk!",
        "category": "satisfying_machinery",
        "content_type": "reel",
        "duration": "5",
        "image_prompt": (
            "Cinematic close-up of a powerful orange forklift lifting a massive pallet "
            "of boxes in a modern warehouse, dramatic side lighting, industrial atmosphere, "
            "9:16 vertical, machinery in motion, dust particles in light beams, "
            "ultra detailed, professional cinematography"
        ),
        "video_prompt": (
            "Smooth cinematic camera tracking a forklift as it lifts a heavy pallet, "
            "dramatic slow motion, industrial warehouse with sunbeams through windows, "
            "9:16 vertical, professional quality, satisfying machinery movement"
        ),
        "caption_uz": "2 tonna yuk — bir harakat! 💪\n\nBRIX.UZ vilkali yuklagichlari — ishonchli va kuchli.\n\nBuyurtma uchun: brix.uz\n\n#brixuz #forklift #sanoat #warehouse #tashkent",
        "voiceover_uz": "Ikki tonna yuk. Bir harakat. BRIX vilkali yuklagichlari — ishingizni osonlashtiradi.",
        "hook": "Ko'ring — 2 tonna bir soniyada! 😱",
        "music_mood": "epic_industrial",
    },
    {
        "id": "brix_02_crane_lift",
        "topic": "Ko'prikli kran — yuqoridan ko'rish",
        "category": "satisfying_machinery",
        "content_type": "reel",
        "duration": "8",
        "image_prompt": (
            "Aerial drone view of an overhead bridge crane lifting a steel beam "
            "in a large factory hall, dramatic industrial lighting, sparks in background, "
            "blue and orange color scheme, 9:16 vertical, cinematic, power and precision"
        ),
        "video_prompt": (
            "Dramatic overhead crane lifting a massive steel beam, camera slowly rising "
            "from floor to ceiling revealing the entire factory, industrial scale, "
            "awe-inspiring, slow motion, 9:16 vertical"
        ),
        "caption_uz": "Ko'prikli kran — tonnalar havoda! 🏗️\n\nBRIX.UZ — har qanday og'irlikdagi yechim.\n\nMaslahat uchun: brix.uz\n\n#brixuz #crane #kran #sanoat #factory",
        "voiceover_uz": "Tonnalar havoda muallaq. Ko'prikli kranlar — BRIX sanoat yechimi. Batafsil: brix.uz",
        "hook": "Bu kran nima ko'tara oladi? 👀",
        "music_mood": "epic_cinematic",
    },
    {
        "id": "brix_03_conveyor_satisfying",
        "topic": "Konveyer liniyasi — hipnotizlovchi harakat",
        "category": "satisfying_machinery",
        "content_type": "reel",
        "duration": "5",
        "image_prompt": (
            "Mesmerizing close-up of products moving along a modern conveyor belt system, "
            "perfectly organized boxes flowing smoothly, LED warehouse lights, "
            "symmetrical composition, 9:16 vertical, satisfying repetitive motion, "
            "clean industrial environment, orange accent lighting"
        ),
        "video_prompt": (
            "Hypnotic satisfying view of a conveyor sorting line in motion, "
            "boxes moving in perfect rhythm, camera following the flow, "
            "clean modern warehouse, smooth motion, 9:16 vertical, ASMR-like quality"
        ),
        "caption_uz": "Buni ko'rib tuxtovsiz qarayman... 😍\n\nKonveyer liniyalari — BRIX.UZ\n\nBuyurtma: brix.uz\n\n#brixuz #conveyor #satisfying #warehouse #logistics",
        "voiceover_uz": "Mukammal tartib. Mukammal harakat. BRIX konveyer liniyalari — samaradorlik yangi darajada.",
        "hook": "Buni ko'rib to'xtay olmaysiz! 😍",
        "music_mood": "chill_satisfying",
    },

    # --- BEHIND THE SCENES ---
    {
        "id": "brix_04_warehouse_transform",
        "topic": "Ombor transformatsiyasi — oldin va keyin",
        "category": "before_after",
        "content_type": "reel",
        "duration": "8",
        "image_prompt": (
            "Split screen showing warehouse transformation: left side chaotic messy warehouse "
            "with scattered boxes, right side perfectly organized modern warehouse with "
            "BRIX equipment, shelving systems, forklifts, clean floor, "
            "dramatic before-and-after, 9:16 vertical, professional lighting"
        ),
        "video_prompt": (
            "Dramatic warehouse transformation reveal, camera starts in a messy chaotic space, "
            "transition effect reveals the same space now perfectly organized with modern equipment, "
            "shelving systems, forklifts, clean lighting, 9:16 vertical, before and after"
        ),
        "caption_uz": "Oldin ↔ Keyin\n\nBRIX.UZ ombor yechimi bilan ishingiz tartibga tushadi!\n\nBepul maslahat: brix.uz\n\n#brixuz #warehouse #transformation #ombor #logistics",
        "voiceover_uz": "Oldin tartibsiz ombor. Keyin — BRIX yechimi. Siz ham omboringizni transformatsiya qiling.",
        "hook": "Bu omborni tanimaysiz! 🤯",
        "music_mood": "reveal_dramatic",
    },
    {
        "id": "brix_05_day_in_life",
        "topic": "BRIX jamoasi kundalik ishlari",
        "category": "behind_the_scenes",
        "content_type": "reel",
        "duration": "10",
        "image_prompt": (
            "Documentary-style photo of BRIX.UZ team members at work: engineers inspecting "
            "a new crane installation, warehouse manager checking inventory on tablet, "
            "technician calibrating a forklift, authentic natural lighting, "
            "9:16 vertical, real people at work, professional yet approachable"
        ),
        "video_prompt": (
            "Day-in-the-life montage of industrial equipment team: morning briefing, "
            "equipment inspection, crane installation, forklift testing, customer handover, "
            "authentic documentary style, natural lighting, 9:16 vertical"
        ),
        "caption_uz": "BRIX jamoasi bilan bir kun 🔧\n\nHar bir mashina ortida — professional jamoa bor.\n\nJamomizga qo'shiling: brix.uz\n\n#brixuz #team #behindthescenes #tashkent #work",
        "voiceover_uz": "Ertalab rejalashtirish. Uskunalarni tekshirish. O'rnatish. Mijozga topshirish. Bu BRIX jamoasining kundalik ishi.",
        "hook": "BRIX jamoasi qanday ishlaydi? 👷",
        "music_mood": "uplifting_corporate",
    },

    # --- EDUCATIONAL ---
    {
        "id": "brix_06_safety_tips",
        "topic": "Omborxona xavfsizligi — 5 ta qoida",
        "category": "safety_tips",
        "content_type": "reel",
        "duration": "10",
        "image_prompt": (
            "Clean infographic-style image showing warehouse safety rules, "
            "worker wearing hard hat and safety vest, forklift with safety markings, "
            "warning signs, modern flat design elements overlaid on warehouse background, "
            "9:16 vertical, educational, professional, orange and blue color scheme"
        ),
        "video_prompt": (
            "Educational video showing 5 warehouse safety rules, numbered countdown format, "
            "each rule demonstrated visually in a real warehouse setting, "
            "safety equipment close-ups, professional narration style, 9:16 vertical"
        ),
        "caption_uz": "Omborxona xavfsizligi — 5 ta muhim qoida! ⚠️\n\n1. Himoya kiyimi\n2. Tezlik chegarasi\n3. Yuk ko'tarish qoidasi\n4. Yo'laklar toza\n5. Signal va ogohlantirish\n\nBRIX.UZ — xavfsiz ish muhiti\n\n#brixuz #safety #xavfsizlik #warehouse #tips",
        "voiceover_uz": "Omborxonada xavfsizlik — birinchi o'rinda! Besh ta muhim qoida. Birinchi: har doim himoya kiyimini kiying.",
        "hook": "Bu qoidalarni bilmasangiz — xavfli! ⚠️",
        "music_mood": "serious_educational",
    },
    {
        "id": "brix_07_forklift_types",
        "topic": "Vilkali yuklagich turlari — qaysi biri sizga mos?",
        "category": "educational",
        "content_type": "reel",
        "duration": "10",
        "image_prompt": (
            "Comparison showcase of different forklift types side by side: "
            "electric counterbalance, reach truck, pallet jack, order picker, "
            "each clearly labeled, warehouse background, professional product photography, "
            "9:16 vertical, clean modern design"
        ),
        "video_prompt": (
            "Educational comparison of forklift types, camera moving from one to another, "
            "each type labeled with name and use case, professional product showcase style, "
            "modern warehouse, 9:16 vertical, smooth transitions"
        ),
        "caption_uz": "Qaysi forklift sizga kerak? 🤔\n\n🔋 Elektr stacker — tor joylar uchun\n🏗️ Counterbalance — og'ir yuklar\n🛒 Palet aravachasi — kundalik ish\n📦 Reach truck — baland javonlar\n\nMaslahat: brix.uz\n\n#brixuz #forklift #types #education #warehouse",
        "voiceover_uz": "Vilkali yuklagichning to'rt turi bor. Qaysi biri sizning omboringizga mos? Keling, birga ko'rib chiqamiz.",
        "hook": "Forkliftlar haqida nima bilasiz? 🤔",
        "music_mood": "educational_upbeat",
    },

    # --- CLIENT STORIES ---
    {
        "id": "brix_08_client_success",
        "topic": "Mijoz hikoyasi — samaradorlik 3 barobar oshdi",
        "category": "client_stories",
        "content_type": "reel",
        "duration": "10",
        "image_prompt": (
            "Professional testimonial-style shot: satisfied factory manager standing proudly "
            "next to new BRIX equipment in a clean modern facility, "
            "before/after statistics overlay, warm professional lighting, "
            "9:16 vertical, trust and success atmosphere"
        ),
        "video_prompt": (
            "Client success story video: factory manager speaks to camera, "
            "cut to equipment in action, overlay statistics showing 3x productivity increase, "
            "professional documentary style, 9:16 vertical, warm lighting"
        ),
        "caption_uz": "Mijozimiz natijasi: samaradorlik 3 barobar oshdi! 📈\n\nBRIX uskunalari bilan ishlab chiqarish yangi darajaga chiqdi.\n\nSiz ham sinab ko'ring: brix.uz\n\n#brixuz #success #client #productivity #uzbekistan",
        "voiceover_uz": "Bizning mijoz aytadi: BRIX uskunalari bilan samaradorlik uch barobar oshdi. Siz ham sinab ko'ring.",
        "hook": "Samaradorlik 3 barobar! Qanday qilib? 📈",
        "music_mood": "success_inspiring",
    },
]


def get_all_briefs() -> list[dict]:
    """Return all BRIX.UZ content briefs."""
    return list(VIRAL_CONTENT_BRIEFS)


def get_brief_by_id(brief_id: str) -> dict | None:
    """Get a specific brief by ID."""
    for brief in VIRAL_CONTENT_BRIEFS:
        if brief["id"] == brief_id:
            return brief
    return None


def get_briefs_by_category(category: str) -> list[dict]:
    """Get briefs filtered by category."""
    return [b for b in VIRAL_CONTENT_BRIEFS if b["category"] == category]
