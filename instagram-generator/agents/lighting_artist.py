"""Lighting Artist Agent (Свет/Художник) — defines visual style, colors, mood.

The Lighting Artist:
  - Sets the color palette and mood for each piece of content
  - Defines lighting setups (golden hour, studio, dramatic, etc.)
  - Ensures visual consistency across carousel slides
  - Provides composition guidelines
  - Adapts visual style to time of day and target audience
"""

from __future__ import annotations

import random
from datetime import datetime
from zoneinfo import ZoneInfo

import structlog

from config import settings
from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

# =====================================================================
# Color palettes
# =====================================================================

COLOR_PALETTES = {
    "golden_warm": {
        "colors": ["#F4A460", "#DAA520", "#CD853F", "#8B4513", "#FFF8DC"],
        "mood": "warm, inviting, nostalgic",
        "best_for": ["motivational", "travel", "recipe", "lifestyle"],
    },
    "cool_blue": {
        "colors": ["#1E3A5F", "#4A90D9", "#87CEEB", "#E0F0FF", "#FFFFFF"],
        "mood": "professional, trustworthy, calm",
        "best_for": ["educational", "tech", "product"],
    },
    "vibrant_pop": {
        "colors": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"],
        "mood": "energetic, youthful, dynamic",
        "best_for": ["fashion", "lifestyle", "humor"],
    },
    "luxury_dark": {
        "colors": ["#1A1A2E", "#16213E", "#C9A96E", "#D4AF37", "#F5F5DC"],
        "mood": "premium, exclusive, sophisticated",
        "best_for": ["product", "fashion"],
    },
    "uzbek_traditional": {
        "colors": ["#1B4D89", "#E8B931", "#C62828", "#FFFFFF", "#2E7D32"],
        "mood": "cultural, authentic, rich heritage",
        "best_for": ["travel", "recipe", "lifestyle"],
    },
    "sunset_cinematic": {
        "colors": ["#FF6F61", "#DE4313", "#7B1FA2", "#1A1A2E", "#FFD700"],
        "mood": "dramatic, cinematic, emotional",
        "best_for": ["motivational", "travel"],
    },
    "fresh_green": {
        "colors": ["#2E7D32", "#66BB6A", "#A5D6A7", "#F1F8E9", "#33691E"],
        "mood": "natural, healthy, organic",
        "best_for": ["recipe", "lifestyle"],
    },
    "neon_tech": {
        "colors": ["#0D0D0D", "#00FF41", "#00D4FF", "#FF00FF", "#1A1A2E"],
        "mood": "futuristic, tech, innovative",
        "best_for": ["tech", "educational"],
    },
    "pastel_soft": {
        "colors": ["#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF"],
        "mood": "gentle, feminine, approachable",
        "best_for": ["lifestyle", "fashion"],
    },
}

# =====================================================================
# Lighting setups
# =====================================================================

LIGHTING_SETUPS = {
    "golden_hour": {
        "description": "warm golden sunlight, long shadows, magic hour",
        "time": "morning/evening",
        "best_for": ["motivational", "travel", "lifestyle"],
    },
    "studio_softbox": {
        "description": "soft diffused studio lighting, even illumination, professional setup",
        "time": "any",
        "best_for": ["product", "fashion"],
    },
    "dramatic_chiaroscuro": {
        "description": "high contrast lighting, deep shadows, dramatic single light source",
        "time": "any",
        "best_for": ["motivational", "fashion"],
    },
    "natural_window": {
        "description": "natural window light, soft shadows, cozy indoor atmosphere",
        "time": "daytime",
        "best_for": ["recipe", "lifestyle", "educational"],
    },
    "neon_glow": {
        "description": "neon colored lighting, cyberpunk atmosphere, RGB glow effects",
        "time": "night",
        "best_for": ["tech", "fashion"],
    },
    "overhead_flat": {
        "description": "flat overhead lighting, minimal shadows, clean and bright",
        "time": "any",
        "best_for": ["recipe", "product", "educational"],
    },
    "backlit_silhouette": {
        "description": "strong backlight, silhouette effect, rim lighting, lens flare",
        "time": "sunset",
        "best_for": ["motivational", "travel"],
    },
    "cinematic_moody": {
        "description": "moody cinematic lighting, teal and orange color grading, film look",
        "time": "any",
        "best_for": ["travel", "motivational", "lifestyle"],
    },
}

# =====================================================================
# Composition rules
# =====================================================================

COMPOSITION_RULES = {
    "reel": {
        "9:16": "vertical composition, subject centered, headroom for text overlay at top/bottom",
        "rule": "Place key visual elements in center-third for mobile viewing",
    },
    "image": {
        "4:5": "portrait composition, rule of thirds, strong focal point",
        "1:1": "square composition, centered subject, balanced elements",
        "rule": "Leave space for caption preview at bottom",
    },
    "carousel": {
        "1:1": "consistent framing across all slides, visual flow left-to-right",
        "rule": "First slide must be scroll-stopping, last slide has CTA",
    },
    "story": {
        "9:16": "full vertical, interactive zones: top for close, middle for content, bottom for reply",
        "rule": "Keep text in safe zones, avoid edges",
    },
}


class LightingArtistAgent(CreativeAgent):
    """Defines the visual identity for each piece of content."""

    role = AgentRole.LIGHTING_ARTIST

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info(
            "lighting_artist.process",
            category=brief.category,
            content_type=brief.content_type,
        )

        # 1. Select color palette
        palette = self._select_palette(brief.category)
        brief.color_palette = palette["colors"]
        if not brief.mood:
            brief.mood = palette["mood"]

        # 2. Set lighting
        lighting = self._select_lighting(brief.category)
        brief.lighting_setup = lighting["description"]

        # 3. Set composition
        brief.composition_notes = self._get_composition(brief.content_type)

        # 4. Add visual references
        brief.visual_references = self._get_references(brief.category)

        # 5. Adapt to time of day
        brief = self._adapt_to_time(brief)

        self.send_message(
            AgentRole.EDITOR,
            "set_visual_style",
            palette=brief.color_palette,
            lighting=brief.lighting_setup,
            mood=brief.mood,
        )

        return brief

    def _select_palette(self, category: str) -> dict:
        """Select the best color palette for the category."""
        suitable = [
            (name, p) for name, p in COLOR_PALETTES.items()
            if category in p["best_for"]
        ]
        if suitable:
            _, palette = random.choice(suitable)
            return palette
        return COLOR_PALETTES["golden_warm"]

    def _select_lighting(self, category: str) -> dict:
        """Select appropriate lighting setup."""
        suitable = [
            (name, l) for name, l in LIGHTING_SETUPS.items()
            if category in l["best_for"]
        ]
        if suitable:
            _, lighting = random.choice(suitable)
            return lighting
        return LIGHTING_SETUPS["golden_hour"]

    def _get_composition(self, content_type: str) -> str:
        """Get composition guidelines for the content type."""
        comp = COMPOSITION_RULES.get(content_type, COMPOSITION_RULES["image"])
        return comp.get("rule", "")

    def _get_references(self, category: str) -> list[str]:
        """Get visual reference keywords."""
        refs = {
            "travel": ["National Geographic", "travel magazine", "drone photography"],
            "recipe": ["Bon Appetit", "food magazine", "overhead food photography"],
            "fashion": ["Vogue", "Harper's Bazaar", "editorial fashion"],
            "product": ["Apple product photography", "luxury brand", "premium catalog"],
            "motivational": ["cinematic photography", "dramatic landscape", "inspirational"],
            "tech": ["Wired magazine", "tech product launch", "futuristic"],
        }
        return refs.get(category, ["professional photography", "high quality"])

    def _adapt_to_time(self, brief: CreativeBrief) -> CreativeBrief:
        """Adjust visual style based on posting time of day."""
        now = datetime.now(ZoneInfo(settings.timezone))
        hour = now.hour

        if 5 <= hour < 11:
            # Morning — warm, bright, energetic
            if "dark" in brief.mood:
                brief.mood = brief.mood.replace("dark", "bright")
            brief.lighting_setup += ", morning light, fresh atmosphere"
        elif 11 <= hour < 16:
            # Afternoon — neutral, clear
            pass  # Keep as-is
        elif 16 <= hour < 21:
            # Evening — cinematic, warm, dramatic
            brief.lighting_setup += ", golden hour warmth"
        else:
            # Night — moody, dramatic
            brief.lighting_setup += ", night atmosphere, artificial lighting"

        return brief
