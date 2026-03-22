"""Editor Agent (Монтажёр) — manages post-production, timing, transitions.

The Editor:
  - Plans scene cuts and timing for Reels
  - Defines transition styles between scenes
  - Configures text overlay placement and animation
  - Sets music mood for background tracks
  - Manages pacing and rhythm of the final video
"""

from __future__ import annotations

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

# =====================================================================
# Transition presets
# =====================================================================

TRANSITION_PRESETS = {
    "smooth": {
        "type": "crossfade",
        "duration_ms": 500,
        "easing": "ease-in-out",
    },
    "smooth_dissolve": {
        "type": "dissolve",
        "duration_ms": 800,
        "easing": "ease-in-out",
    },
    "clean_cut": {
        "type": "cut",
        "duration_ms": 0,
        "easing": "none",
    },
    "zoom_snap": {
        "type": "zoom",
        "duration_ms": 300,
        "easing": "ease-out",
        "scale": 1.2,
    },
    "slide_left": {
        "type": "slide",
        "direction": "left",
        "duration_ms": 400,
        "easing": "ease-in-out",
    },
    "whip_pan": {
        "type": "whip",
        "duration_ms": 200,
        "motion_blur": True,
    },
}

# =====================================================================
# Text overlay configurations
# =====================================================================

TEXT_OVERLAY_PRESETS = {
    "hook_top": {
        "position": "top",
        "font_size": 56,
        "font_weight": "bold",
        "font_color": "#FFFFFF",
        "bg_color": "rgba(0,0,0,0.6)",
        "padding": 16,
        "animation": "fade_in",
        "duration_ms": 2000,
    },
    "subtitle_bottom": {
        "position": "bottom",
        "font_size": 42,
        "font_weight": "normal",
        "font_color": "#FFFFFF",
        "bg_color": "rgba(0,0,0,0.5)",
        "padding": 12,
        "animation": "word_by_word",
        "duration_ms": None,  # matches voiceover
    },
    "cta_center": {
        "position": "center",
        "font_size": 64,
        "font_weight": "bold",
        "font_color": "#FFFFFF",
        "bg_color": "rgba(0,0,0,0.7)",
        "padding": 24,
        "animation": "scale_up",
        "duration_ms": 1500,
    },
    "info_left": {
        "position": "bottom_left",
        "font_size": 36,
        "font_weight": "normal",
        "font_color": "#FFFFFF",
        "bg_color": "transparent",
        "text_shadow": True,
        "animation": "slide_in",
        "duration_ms": 1000,
    },
}

# =====================================================================
# Music mood mapping
# =====================================================================

MUSIC_MOODS = {
    "motivational": {
        "mood": "epic_inspiring",
        "bpm_range": (100, 130),
        "instruments": ["piano", "strings", "drums"],
        "energy": "building",
    },
    "educational": {
        "mood": "chill_focus",
        "bpm_range": (80, 100),
        "instruments": ["lo-fi beats", "soft piano"],
        "energy": "steady",
    },
    "product": {
        "mood": "modern_upbeat",
        "bpm_range": (110, 140),
        "instruments": ["synth", "bass", "claps"],
        "energy": "high",
    },
    "travel": {
        "mood": "cinematic_adventure",
        "bpm_range": (90, 120),
        "instruments": ["orchestral", "world music", "flute"],
        "energy": "flowing",
    },
    "recipe": {
        "mood": "warm_acoustic",
        "bpm_range": (80, 110),
        "instruments": ["acoustic guitar", "ukulele", "light percussion"],
        "energy": "cozy",
    },
    "fashion": {
        "mood": "trendy_beat",
        "bpm_range": (110, 135),
        "instruments": ["trap beats", "synth", "bass"],
        "energy": "confident",
    },
    "tech": {
        "mood": "electronic_future",
        "bpm_range": (120, 150),
        "instruments": ["synth", "electronic", "glitch"],
        "energy": "innovative",
    },
    "lifestyle": {
        "mood": "feel_good",
        "bpm_range": (90, 120),
        "instruments": ["acoustic", "soft pop", "keys"],
        "energy": "positive",
    },
    "humor": {
        "mood": "fun_playful",
        "bpm_range": (100, 130),
        "instruments": ["quirky sounds", "upbeat pop"],
        "energy": "playful",
    },
}

# =====================================================================
# Pacing templates (scene timing)
# =====================================================================

PACING_TEMPLATES = {
    "cinematic_slow": {
        "5s": [
            {"start": 0.0, "end": 2.0, "scene": "establishing", "motion": "slow_zoom_in"},
            {"start": 2.0, "end": 4.0, "scene": "main", "motion": "slow_pan"},
            {"start": 4.0, "end": 5.0, "scene": "closing", "motion": "fade_out"},
        ],
        "10s": [
            {"start": 0.0, "end": 3.0, "scene": "establishing", "motion": "slow_zoom_in"},
            {"start": 3.0, "end": 5.0, "scene": "reveal", "motion": "dolly_forward"},
            {"start": 5.0, "end": 8.0, "scene": "main", "motion": "slow_orbit"},
            {"start": 8.0, "end": 10.0, "scene": "closing", "motion": "pull_back"},
        ],
    },
    "dynamic_fast": {
        "5s": [
            {"start": 0.0, "end": 0.8, "scene": "hook", "motion": "snap_zoom"},
            {"start": 0.8, "end": 2.0, "scene": "detail_1", "motion": "whip_pan"},
            {"start": 2.0, "end": 3.5, "scene": "detail_2", "motion": "rotate"},
            {"start": 3.5, "end": 4.5, "scene": "reveal", "motion": "zoom_out"},
            {"start": 4.5, "end": 5.0, "scene": "cta", "motion": "scale_up"},
        ],
        "10s": [
            {"start": 0.0, "end": 1.0, "scene": "hook", "motion": "snap_zoom"},
            {"start": 1.0, "end": 3.0, "scene": "detail_1", "motion": "rapid_cuts"},
            {"start": 3.0, "end": 5.0, "scene": "detail_2", "motion": "dynamic_pan"},
            {"start": 5.0, "end": 7.0, "scene": "climax", "motion": "whip_pan"},
            {"start": 7.0, "end": 9.0, "scene": "detail_3", "motion": "zoom_in"},
            {"start": 9.0, "end": 10.0, "scene": "cta", "motion": "scale_up"},
        ],
    },
    "moderate": {
        "5s": [
            {"start": 0.0, "end": 1.5, "scene": "intro", "motion": "gentle_zoom"},
            {"start": 1.5, "end": 3.5, "scene": "main", "motion": "slow_pan"},
            {"start": 3.5, "end": 5.0, "scene": "outro", "motion": "fade"},
        ],
        "10s": [
            {"start": 0.0, "end": 2.5, "scene": "intro", "motion": "gentle_zoom"},
            {"start": 2.5, "end": 5.0, "scene": "develop", "motion": "pan_right"},
            {"start": 5.0, "end": 7.5, "scene": "climax", "motion": "zoom_in"},
            {"start": 7.5, "end": 10.0, "scene": "outro", "motion": "pull_back"},
        ],
    },
}


class EditorAgent(CreativeAgent):
    """Manages post-production: timing, transitions, overlays, music."""

    role = AgentRole.EDITOR

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        logger.info(
            "editor.process",
            content_type=brief.content_type,
            pacing=brief.pacing,
        )

        if brief.content_type in ("reel", "story"):
            # 1. Plan scene cuts
            brief.scene_cuts = self._plan_scene_cuts(brief)

            # 2. Set transition style
            if brief.transition_style in TRANSITION_PRESETS:
                pass  # Already set by Director
            else:
                brief.transition_style = "smooth"

            # 3. Configure text overlays
            brief.text_overlay_config = self._configure_overlays(brief)

            # 4. Set music mood
            brief.music_mood = self._select_music(brief.category)

        return brief

    def _plan_scene_cuts(self, brief: CreativeBrief) -> list[dict]:
        """Plan scene timing based on pacing and duration."""
        pacing = brief.pacing or "moderate"
        duration = brief.duration or "5"

        template = PACING_TEMPLATES.get(pacing, PACING_TEMPLATES["moderate"])
        scenes = template.get(f"{duration}s", template.get("5s", []))

        # Enrich scenes with content from script
        enriched = []
        script_lines = brief.script.strip().split("\n") if brief.script else []

        for i, scene in enumerate(scenes):
            enriched_scene = dict(scene)
            if i < len(script_lines):
                enriched_scene["description"] = script_lines[i].strip()
            enriched.append(enriched_scene)

        return enriched

    def _configure_overlays(self, brief: CreativeBrief) -> dict:
        """Configure text overlay positioning and style."""
        config = {
            "layers": [],
        }

        # Hook text at the top (first 2 seconds)
        if brief.hook_line:
            config["layers"].append({
                **TEXT_OVERLAY_PRESETS["hook_top"],
                "text": brief.hook_line,
                "start_time": 0.0,
                "end_time": 2.0,
            })

        # Subtitle text at bottom
        if brief.subtitle_text:
            config["layers"].append({
                **TEXT_OVERLAY_PRESETS["subtitle_bottom"],
                "text": brief.subtitle_text,
                "start_time": 0.5,
                "end_time": float(brief.duration) - 0.5,
            })

        # CTA at the end
        if brief.cta:
            config["layers"].append({
                **TEXT_OVERLAY_PRESETS["cta_center"],
                "text": brief.cta,
                "start_time": float(brief.duration) - 2.0,
                "end_time": float(brief.duration),
            })

        # Apply color palette to overlays
        if brief.color_palette:
            accent = brief.color_palette[0] if brief.color_palette else "#FFFFFF"
            for layer in config["layers"]:
                if layer.get("animation") == "scale_up":
                    layer["font_color"] = accent

        return config

    def _select_music(self, category: str) -> str:
        """Select music mood based on content category."""
        music = MUSIC_MOODS.get(category, MUSIC_MOODS["lifestyle"])
        return music["mood"]
