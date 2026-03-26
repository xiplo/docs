"""Prompt Engineer Agent v2 — optimized for Flux + Kling 2.5 via PiAPI.

Upgraded for 2026 models:
  - Flux (flux1-dev): Natural language prompts, no token weighting needed
  - Kling 2.5: Motion-focused prompts, camera control directives
  - Seedance 2.0: Cinematic video descriptions
  - Negative prompts simplified (Flux handles them internally)

Best practices (2026):
  - Flux: Descriptive sentences > keyword lists
  - Kling 2.5: Explicit motion + camera + timing cues
  - 9:16 vertical for Reels/TikTok/Shorts
"""

from __future__ import annotations

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

QUALITY_BOOSTERS = [
    "ultra detailed", "high resolution", "professional photography",
    "sharp focus", "masterpiece", "best quality",
]

NEGATIVE_PROMPTS = {
    "universal": (
        "blurry, low quality, watermark, text, logo, banner, "
        "deformed, disfigured, bad anatomy, extra limbs, "
        "duplicate, ugly, distorted, oversaturated"
    ),
    "food": (
        "blurry, low quality, watermark, text, logo, "
        "unappetizing, moldy, burnt, artificial looking, "
        "dirty plate, messy background"
    ),
    "portrait": (
        "blurry, low quality, watermark, text, logo, "
        "deformed face, bad anatomy, extra fingers, "
        "cross-eyed, distorted features"
    ),
    "landscape": (
        "blurry, low quality, watermark, text, logo, "
        "oversaturated, HDR artifacts, lens flare, "
        "power lines, modern buildings in historical scene"
    ),
}

# Flux-optimized style presets (natural language, 2026)
FLUX_STYLES = {
    "cinematic": {
        "prefix": "Cinematic still frame, film grain, anamorphic lens, ",
        "suffix": ", dramatic lighting, color graded, shallow depth of field, 35mm film look",
    },
    "photorealistic": {
        "prefix": "RAW photograph, DSLR, ",
        "suffix": ", natural lighting, depth of field, sharp focus, professional photography",
    },
    "editorial": {
        "prefix": "Editorial magazine photograph, high fashion, ",
        "suffix": ", studio lighting, clean composition, Vogue style",
    },
    "aerial": {
        "prefix": "Aerial drone photograph, bird's eye view, ",
        "suffix": ", wide angle, golden hour, epic scale, DJI quality",
    },
    "food_photo": {
        "prefix": "Professional food photography, overhead flat lay, ",
        "suffix": ", appetizing, steam rising, rustic wooden table, natural window light",
    },
    "flat_design": {
        "prefix": "Modern flat design illustration, clean vectors, ",
        "suffix": ", minimalist, bold colors, geometric shapes, UI design",
    },
    "artistic": {
        "prefix": "Digital art, trending on Artstation, ",
        "suffix": ", vibrant colors, highly detailed, concept art quality",
    },
}

# Category-specific visual prompts for Uzbekistan
CATEGORY_VISUALS = {
    "motivational": [
        "dramatic lighting", "golden hour", "epic scale",
        "inspirational atmosphere", "hero shot",
    ],
    "educational": [
        "clean layout", "organized", "infographic style",
        "clear visual hierarchy", "modern design",
    ],
    "product": [
        "studio lighting", "product photography", "premium feel",
        "bokeh background", "luxury aesthetic",
    ],
    "travel": [
        "drone photography", "wide angle", "panoramic",
        "golden hour", "Silk Road architecture", "turquoise mosaic",
    ],
    "recipe": [
        "food photography", "overhead shot", "rustic table",
        "steam rising", "fresh ingredients", "appetizing",
    ],
    "lifestyle": [
        "natural light", "cozy atmosphere", "candid moment",
        "warm tones", "authentic feel",
    ],
    "fitness": [
        "dynamic action shot", "gym lighting",
        "energetic movement", "athletic pose",
    ],
}

UZBEK_VISUAL_ELEMENTS = {
    "architecture": [
        "Registan square Samarkand", "Kalyan minaret Bukhara",
        "Ichan-Kala Khiva", "Tashkent City Park",
        "turquoise mosaic tilework", "Islamic geometric patterns",
    ],
    "food": [
        "Uzbek plov in kazan", "samsa from tandoor",
        "fresh Uzbek non bread", "chaikhana tea house",
    ],
    "nature": [
        "Chimgan mountains", "Charvak lake",
        "Kyzylkum desert sunset", "Fergana valley",
    ],
}


class PromptEngineerAgent(CreativeAgent):
    """Crafts optimized prompts for Flux (images) and Kling 2.5 (video)."""

    role = AgentRole.PROMPT_ENGINEER

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info(
            "prompt_engineer.process",
            content_type=brief.content_type,
            style=brief.style_preset,
        )

        brief.image_prompt = self._build_image_prompt(brief)
        brief.negative_prompt = self._build_negative_prompt(brief)

        if brief.content_type == "reel":
            brief.video_prompt = self._build_video_prompt(brief)

        if brief.content_type == "carousel":
            brief.carousel_prompts = self._build_carousel_prompts(brief)

        self.send_message(
            AgentRole.LIGHTING_ARTIST,
            "set_visual_style",
            image_prompt=brief.image_prompt,
            mood=brief.mood,
        )

        return brief

    def _build_image_prompt(self, brief: CreativeBrief) -> str:
        """Build a Flux-optimized image prompt (natural language style)."""
        parts = []

        # Style prefix (Flux prefers descriptive sentences)
        style = FLUX_STYLES.get(brief.style_preset, FLUX_STYLES["cinematic"])
        parts.append(style["prefix"])

        # Main subject
        parts.append(brief.topic)

        # Category visuals
        cat_visuals = CATEGORY_VISUALS.get(brief.category, [])
        if cat_visuals:
            parts.append(", ".join(cat_visuals[:3]))

        # Lighting (from LightingArtist if set)
        if brief.lighting_setup:
            parts.append(brief.lighting_setup)

        # Color palette
        if brief.color_palette:
            parts.append(f"color palette: {', '.join(brief.color_palette[:4])}")

        # Mood
        if brief.mood:
            parts.append(f"{brief.mood} atmosphere")

        # Composition
        if brief.composition_notes:
            parts.append(brief.composition_notes)

        # Quality
        parts.extend(QUALITY_BOOSTERS[:3])

        # Style suffix
        parts.append(style["suffix"])

        prompt = ", ".join(p.strip().strip(",") for p in parts if p.strip())
        logger.info("prompt_engineer.image_prompt", length=len(prompt))
        return prompt

    def _build_negative_prompt(self, brief: CreativeBrief) -> str:
        if brief.category == "recipe":
            return NEGATIVE_PROMPTS["food"]
        elif brief.category == "travel":
            return NEGATIVE_PROMPTS["landscape"]
        return NEGATIVE_PROMPTS["universal"]

    def _build_video_prompt(self, brief: CreativeBrief) -> str:
        """Build a Kling 2.5 / Seedance optimized video prompt."""
        motion_map = {
            "cinematic_slow": "slow cinematic dolly shot, smooth camera glide, epic reveal",
            "dynamic_fast": "dynamic handheld camera, fast cuts, energetic movement, action",
            "moderate": "gentle camera pan, natural movement, steady tracking shot",
        }
        motion = motion_map.get(brief.pacing, motion_map["moderate"])

        return (
            f"{brief.topic}, {motion}, "
            f"professional cinematography, {brief.mood or 'engaging'} mood, "
            f"smooth motion, high production value, 9:16 vertical"
        )

    def _build_carousel_prompts(self, brief: CreativeBrief) -> list[str]:
        style = FLUX_STYLES.get(brief.style_preset, FLUX_STYLES["flat_design"])
        base = f"{style['prefix']}consistent style, modern design{style['suffix']}"

        return [
            f"{base}, title slide, bold typography, '{brief.hook_line}'",
            f"{base}, informational slide about {brief.topic}, key points",
            f"{base}, detailed breakdown of {brief.topic}, icons and visuals",
            f"{base}, call to action slide, '{brief.cta}'",
        ]
