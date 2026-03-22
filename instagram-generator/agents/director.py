"""Director Agent (Режиссёр) — orchestrates the entire creative process.

The Director:
  - Analyzes the content brief and decides the creative direction
  - Assigns tasks to other agents
  - Reviews intermediary outputs and requests revisions
  - Makes final approval decisions
  - Manages the overall creative vision and coherence
"""

from __future__ import annotations

import structlog

from .base import AgentRole, CreativeAgent, CreativeBrief

logger = structlog.get_logger(__name__)

# Director's decision rules for content type → agent pipeline
PIPELINE_CONFIGS = {
    "reel": {
        "agents": ["screenwriter", "prompt_engineer", "lighting_artist", "editor"],
        "requires_voiceover": True,
        "requires_video": True,
        "max_duration": "10",
        "aspect_ratio": "9:16",
    },
    "image": {
        "agents": ["screenwriter", "prompt_engineer", "lighting_artist"],
        "requires_voiceover": False,
        "requires_video": False,
        "aspect_ratio": "4:5",
    },
    "carousel": {
        "agents": ["screenwriter", "prompt_engineer", "lighting_artist"],
        "requires_voiceover": False,
        "requires_video": False,
        "min_slides": 3,
        "max_slides": 10,
        "aspect_ratio": "1:1",
    },
    "story": {
        "agents": ["prompt_engineer", "lighting_artist"],
        "requires_voiceover": False,
        "requires_video": False,
        "aspect_ratio": "9:16",
    },
}

# Time-of-day content strategy
TIME_STRATEGY = {
    "morning": {
        "mood": "energetic, inspiring, fresh",
        "categories": ["motivational", "educational", "lifestyle"],
        "color_temp": "warm golden",
    },
    "afternoon": {
        "mood": "informative, engaging, dynamic",
        "categories": ["educational", "product", "tech"],
        "color_temp": "bright neutral",
    },
    "evening": {
        "mood": "reflective, cinematic, emotional",
        "categories": ["lifestyle", "travel", "fashion", "recipe"],
        "color_temp": "warm sunset / moody",
    },
}


class DirectorAgent(CreativeAgent):
    """The Director orchestrates all other agents."""

    role = AgentRole.DIRECTOR

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        """Analyze brief, set creative direction, enrich with director's vision."""
        logger.info(
            "director.process",
            topic=brief.topic,
            content_type=brief.content_type,
        )

        config = PIPELINE_CONFIGS.get(brief.content_type, PIPELINE_CONFIGS["reel"])

        # Set creative direction based on content type
        brief = self._set_creative_direction(brief, config)

        self.send_message(
            AgentRole.SCREENWRITER,
            "write_script",
            topic=brief.topic,
            content_type=brief.content_type,
            brand_voice=brief.brand_voice,
        )

        return brief

    def _set_creative_direction(
        self, brief: CreativeBrief, config: dict
    ) -> CreativeBrief:
        """Director's creative decisions based on content type and category."""

        # Decide pacing based on content type
        if brief.content_type == "reel":
            if brief.category in ("motivational", "travel"):
                brief.pacing = "cinematic_slow"
            elif brief.category in ("product", "tech"):
                brief.pacing = "dynamic_fast"
            else:
                brief.pacing = "moderate"

        # Set transition style
        if brief.category == "educational":
            brief.transition_style = "clean_cut"
        elif brief.category in ("travel", "lifestyle"):
            brief.transition_style = "smooth_dissolve"
        elif brief.category == "product":
            brief.transition_style = "zoom_snap"
        else:
            brief.transition_style = "smooth"

        return brief

    def evaluate_quality(self, brief: CreativeBrief) -> bool:
        """Director's final quality gate."""
        scores = brief.quality_scores
        if not scores:
            return False

        avg = sum(scores.values()) / len(scores) if scores else 0
        # Director requires average score >= 7.0
        if avg < 7.0:
            logger.warning("director.quality_gate_failed", avg_score=avg)
            return False

        # Check critical metrics
        if scores.get("brand_alignment", 0) < 6.0:
            return False
        if scores.get("cultural_sensitivity", 0) < 8.0:
            return False

        brief.approved = True
        logger.info("director.approved", avg_score=avg)
        return True
