"""Creative Crew — orchestrates the full multi-agent pipeline.

The Crew manages the sequential agent pipeline:
  1. Director   → sets creative direction
  2. Screenwriter → writes script, caption, voiceover
  3. PromptEngineer → crafts AI generation prompts
  4. LightingArtist → sets visual style and colors
  5. Editor → plans post-production
  6. QualityReviewer → scores and approves/rejects

If quality review fails, the crew loops back for revisions (max 3 attempts).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from config import settings
from .base import CreativeBrief
from .director import DirectorAgent
from .screenwriter import ScreenwriterAgent
from .prompt_engineer import PromptEngineerAgent
from .lighting_artist import LightingArtistAgent
from .editor import EditorAgent
from .quality_reviewer import QualityReviewerAgent

logger = structlog.get_logger(__name__)

MAX_REVISION_ROUNDS = 3


class CreativeCrew:
    """Orchestrates all creative agents in a pipeline."""

    def __init__(self) -> None:
        self.director = DirectorAgent()
        self.screenwriter = ScreenwriterAgent()
        self.prompt_engineer = PromptEngineerAgent()
        self.lighting_artist = LightingArtistAgent()
        self.editor = EditorAgent()
        self.quality_reviewer = QualityReviewerAgent()

    async def produce(
        self,
        topic: str,
        category: str,
        content_type: str = "reel",
        *,
        brand_voice: str = "inspiring, modern, culturally authentic",
        target_audience: str = "Uzbek-speaking Instagram users, 18-35",
        duration: str = "5",
        style_preset: str = "photorealistic",
    ) -> CreativeBrief:
        """Run the full creative pipeline and return the approved brief.

        Args:
            topic: What the content is about
            category: Content category (motivational, educational, etc.)
            content_type: reel, image, carousel, story
            brand_voice: Brand voice description
            target_audience: Target audience description
            duration: Video duration in seconds (for reels)
            style_preset: Visual style preset

        Returns:
            CreativeBrief with all fields populated and quality-approved
        """
        brief = CreativeBrief(
            topic=topic,
            category=category,
            content_type=content_type,
            brand_voice=brand_voice,
            target_audience=target_audience,
            duration=duration,
            style_preset=style_preset,
        )

        logger.info(
            "crew.start",
            topic=topic,
            category=category,
            content_type=content_type,
        )

        for attempt in range(1, MAX_REVISION_ROUNDS + 1):
            logger.info("crew.round", attempt=attempt)

            # Run the pipeline
            brief = await self.director.process(brief)
            brief = await self.screenwriter.process(brief)
            brief = await self.prompt_engineer.process(brief)
            brief = await self.lighting_artist.process(brief)
            brief = await self.editor.process(brief)
            brief = await self.quality_reviewer.process(brief)

            if brief.approved:
                logger.info("crew.approved", attempt=attempt)
                break

            if attempt < MAX_REVISION_ROUNDS:
                logger.warning(
                    "crew.revision_needed",
                    attempt=attempt,
                    notes=brief.revision_notes,
                )
            else:
                logger.error(
                    "crew.max_revisions_reached",
                    notes=brief.revision_notes,
                )

        # Save the brief for audit/debugging
        self._save_brief(brief)

        return brief

    def brief_to_content_request(self, brief: CreativeBrief) -> dict[str, Any]:
        """Convert a CreativeBrief into ContentRequest-compatible dict.

        This bridges the agent system with the generation pipeline.
        """
        return {
            "content_type": brief.content_type,
            "image_prompt": brief.image_prompt,
            "caption": brief.caption,
            "voiceover_text": brief.voiceover_text,
            "image_style": brief.style_preset,
            "video_duration": brief.duration,
            "subtitle_text": brief.subtitle_text,
            "carousel_prompts": brief.carousel_prompts,
            "hashtags": brief.hashtags,
        }

    def _save_brief(self, brief: CreativeBrief) -> None:
        """Save the creative brief to disk for audit."""
        audit_dir = settings.content_output_dir / "briefs"
        audit_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = audit_dir / f"brief_{ts}_{brief.content_type}.json"

        data = {
            "topic": brief.topic,
            "category": brief.category,
            "content_type": brief.content_type,
            "approved": brief.approved,
            "quality_scores": brief.quality_scores,
            "revision_notes": brief.revision_notes,
            "image_prompt": brief.image_prompt,
            "negative_prompt": brief.negative_prompt,
            "video_prompt": brief.video_prompt,
            "caption": brief.caption,
            "voiceover_text": brief.voiceover_text,
            "hook_line": brief.hook_line,
            "cta": brief.cta,
            "hashtags": brief.hashtags,
            "color_palette": brief.color_palette,
            "lighting_setup": brief.lighting_setup,
            "mood": brief.mood,
            "pacing": brief.pacing,
            "transition_style": brief.transition_style,
            "scene_cuts": brief.scene_cuts,
            "text_overlay_config": brief.text_overlay_config,
            "music_mood": brief.music_mood,
            "script": brief.script,
        }

        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        logger.info("crew.brief_saved", path=str(path))
