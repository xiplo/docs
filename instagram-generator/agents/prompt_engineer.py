"""Prompt Engineer Agent (Промт-инженер) — crafts optimized prompts for AI models.

The Prompt Engineer:
  - Translates the Director's vision into precise AI model prompts
  - Optimizes prompts for Nano Banana (image gen) and Kling 3.0 (video gen)
  - Manages negative prompts to avoid common artifacts
  - Adapts prompt style based on the target model
  - Handles carousel slide prompt consistency
"""

from __future__ import annotations

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

# =====================================================================
# Prompt engineering building blocks
# =====================================================================

QUALITY_BOOSTERS = [
    "ultra detailed", "high resolution", "professional photography",
    "sharp focus", "masterpiece", "best quality",
]

NEGATIVE_PROMPTS = {
    "universal": (
        "blurry, low quality, watermark, text, logo, banner, "
        "deformed, disfigured, bad anatomy, extra limbs, "
        "duplicate, morbid, mutilated, poorly drawn, "
        "ugly, distorted, oversaturated, underexposed"
    ),
    "food": (
        "blurry, low quality, watermark, text, logo, "
        "unappetizing, moldy, burnt, raw, undercooked, "
        "dirty plate, messy background, artificial looking"
    ),
    "portrait": (
        "blurry, low quality, watermark, text, logo, "
        "deformed face, bad anatomy, extra fingers, "
        "cross-eyed, distorted features, uncanny valley"
    ),
    "landscape": (
        "blurry, low quality, watermark, text, logo, "
        "oversaturated, HDR artifacts, lens flare, "
        "power lines, modern buildings in historical scene"
    ),
}

STYLE_MODIFIERS = {
    "photorealistic": {
        "prefix": "RAW photo, ",
        "suffix": ", DSLR, 35mm film, natural lighting, depth of field",
        "negative_extra": "cartoon, anime, illustration, painting, drawing",
    },
    "illustration": {
        "prefix": "Digital illustration, ",
        "suffix": ", trending on Artstation, highly detailed illustration",
        "negative_extra": "photograph, photo, realistic, 3d render",
    },
    "3d_render": {
        "prefix": "3D render, ",
        "suffix": ", octane render, cinema 4D, subsurface scattering, volumetric lighting",
        "negative_extra": "flat, 2d, photograph, sketch",
    },
    "cinematic": {
        "prefix": "Cinematic still, ",
        "suffix": ", anamorphic lens, film grain, color graded, dramatic lighting",
        "negative_extra": "amateur, low budget, flat lighting",
    },
    "anime": {
        "prefix": "Anime style, ",
        "suffix": ", Studio Ghibli inspired, beautiful detailed eyes, vibrant colors",
        "negative_extra": "realistic, photograph, 3d",
    },
    "flat_design": {
        "prefix": "Modern flat design, ",
        "suffix": ", clean vectors, minimalist, bold colors, UI design",
        "negative_extra": "realistic, photograph, 3d, gradient",
    },
    "watercolor": {
        "prefix": "Watercolor painting, ",
        "suffix": ", soft washes, wet on wet technique, artistic, delicate",
        "negative_extra": "digital, photograph, sharp lines",
    },
}

# Category-specific visual keywords
CATEGORY_VISUALS = {
    "motivational": [
        "dramatic lighting", "golden hour", "epic scale",
        "inspirational atmosphere", "hero shot",
    ],
    "educational": [
        "clean layout", "organized composition", "infographic style",
        "clear visual hierarchy", "modern design",
    ],
    "product": [
        "studio lighting", "product photography", "premium feel",
        "bokeh background", "luxury aesthetic",
    ],
    "travel": [
        "drone photography", "wide angle", "panoramic",
        "golden hour", "epic landscape", "aerial view",
    ],
    "recipe": [
        "food photography", "overhead shot", "rustic table",
        "steam rising", "fresh ingredients", "appetizing",
    ],
    "fashion": [
        "editorial photography", "studio shot", "fashion magazine",
        "high fashion", "elegant lighting", "model pose",
    ],
    "tech": [
        "futuristic", "neon glow", "dark theme",
        "holographic", "tech aesthetic", "modern workspace",
    ],
    "lifestyle": [
        "natural light", "cozy atmosphere", "candid moment",
        "warm tones", "authentic feel", "lifestyle photography",
    ],
}

# Uzbekistan-specific visual elements
UZBEK_VISUAL_ELEMENTS = {
    "architecture": [
        "Registan square Samarkand", "Kalyan minaret Bukhara",
        "Ichan-Kala Khiva", "Tashkent TV tower",
        "Amir Timur square", "Chorsu bazaar",
        "Islamic geometric patterns", "turquoise mosaic tilework",
    ],
    "nature": [
        "Chimgan mountains", "Charvak lake",
        "Kyzylkum desert sunset", "Fergana valley",
        "Tian Shan mountains", "cotton fields",
    ],
    "culture": [
        "Uzbek suzani embroidery", "atlas ikat fabric",
        "traditional doppi hat", "Uzbek ceramics",
        "silk road marketplace", "Uzbek tea ceremony",
    ],
    "food": [
        "Uzbek plov in kazan", "samsa from tandoor",
        "shashlik on mangal", "fresh Uzbek bread non",
        "chaikhana tea house", "Uzbek dried fruits",
    ],
}


class PromptEngineerAgent(CreativeAgent):
    """Crafts optimized prompts for AI image and video generation."""

    role = AgentRole.PROMPT_ENGINEER

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info(
            "prompt_engineer.process",
            content_type=brief.content_type,
            style=brief.style_preset,
            category=brief.category,
        )

        # 1. Build the main image prompt
        brief.image_prompt = self._build_image_prompt(brief)

        # 2. Build negative prompt
        brief.negative_prompt = self._build_negative_prompt(brief)

        # 3. Build video prompt if needed
        if brief.content_type == "reel":
            brief.video_prompt = self._build_video_prompt(brief)

        # 4. Build carousel prompts if needed
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
        """Assemble an optimized image generation prompt."""
        parts = []

        # Style prefix
        style = STYLE_MODIFIERS.get(brief.style_preset, STYLE_MODIFIERS["photorealistic"])
        parts.append(style["prefix"])

        # Main subject from topic
        parts.append(brief.topic)

        # Category-specific visuals
        cat_visuals = CATEGORY_VISUALS.get(brief.category, [])
        if cat_visuals:
            parts.append(", ".join(cat_visuals[:3]))

        # Lighting from LightingArtist (if set)
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

        # Quality boosters
        parts.extend(QUALITY_BOOSTERS[:3])

        # Style suffix
        parts.append(style["suffix"])

        prompt = ", ".join(p.strip().strip(",") for p in parts if p.strip())
        logger.info("prompt_engineer.image_prompt", length=len(prompt))
        return prompt

    def _build_negative_prompt(self, brief: CreativeBrief) -> str:
        """Build a negative prompt to avoid common issues."""
        # Select base negative by category
        if brief.category == "recipe":
            base = NEGATIVE_PROMPTS["food"]
        elif brief.category == "fashion":
            base = NEGATIVE_PROMPTS["portrait"]
        elif brief.category == "travel":
            base = NEGATIVE_PROMPTS["landscape"]
        else:
            base = NEGATIVE_PROMPTS["universal"]

        # Add style-specific negatives
        style = STYLE_MODIFIERS.get(brief.style_preset, {})
        extra = style.get("negative_extra", "")

        return f"{base}, {extra}" if extra else base

    def _build_video_prompt(self, brief: CreativeBrief) -> str:
        """Build a prompt for Kling 3.0 video generation."""
        motion_styles = {
            "cinematic_slow": "slow cinematic camera movement, smooth dolly shot",
            "dynamic_fast": "dynamic camera movement, fast cuts, energetic",
            "moderate": "gentle camera pan, natural movement",
        }

        motion = motion_styles.get(brief.pacing, motion_styles["moderate"])

        return (
            f"{brief.topic}, {motion}, "
            f"professional video quality, {brief.mood or 'engaging'} atmosphere, "
            f"smooth motion, high production value"
        )

    def _build_carousel_prompts(self, brief: CreativeBrief) -> list[str]:
        """Build consistent prompts for each carousel slide."""
        style = STYLE_MODIFIERS.get(brief.style_preset, STYLE_MODIFIERS["flat_design"])

        # Parse script for slide content if available
        base_style = (
            f"{style['prefix']}clean modern design, consistent style, "
            f"{brief.mood or 'professional'} atmosphere{style['suffix']}"
        )

        # Default: create 4 slides
        slides = [
            f"{base_style}, title slide with text '{brief.hook_line}', bold typography, eye-catching",
            f"{base_style}, informational slide about {brief.topic}, key points visualization",
            f"{base_style}, detailed breakdown of {brief.topic}, icons and visual elements",
            f"{base_style}, call to action slide, engaging design, '{brief.cta}'",
        ]

        return slides
