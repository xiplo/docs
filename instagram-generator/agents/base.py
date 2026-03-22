"""Base classes for the multi-agent creative system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AgentRole(str, Enum):
    DIRECTOR = "director"
    SCREENWRITER = "screenwriter"
    PROMPT_ENGINEER = "prompt_engineer"
    LIGHTING_ARTIST = "lighting_artist"
    EDITOR = "editor"
    QUALITY_REVIEWER = "quality_reviewer"


@dataclass
class AgentMessage:
    """Message passed between agents in the pipeline."""

    sender: AgentRole
    recipient: AgentRole
    action: str
    payload: dict[str, Any] = field(default_factory=dict)
    notes: str = ""


@dataclass
class CreativeBrief:
    """The creative brief that flows through the agent pipeline."""

    # Input
    topic: str = ""
    category: str = ""
    content_type: str = "reel"  # reel, image, carousel, story
    target_audience: str = "Uzbek-speaking Instagram users, 18-35"
    brand_voice: str = "inspiring, modern, culturally authentic"
    language: str = "uz"
    duration: str = "5"

    # Filled by Screenwriter
    script: str = ""
    voiceover_text: str = ""
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    hook_line: str = ""
    cta: str = ""

    # Filled by PromptEngineer
    image_prompt: str = ""
    negative_prompt: str = ""
    video_prompt: str = ""
    carousel_prompts: list[str] = field(default_factory=list)
    style_preset: str = "photorealistic"

    # Filled by LightingArtist
    color_palette: list[str] = field(default_factory=list)
    lighting_setup: str = ""
    mood: str = ""
    visual_references: list[str] = field(default_factory=list)
    composition_notes: str = ""

    # Filled by Editor
    scene_cuts: list[dict] = field(default_factory=list)
    transition_style: str = "smooth"
    text_overlay_config: dict = field(default_factory=dict)
    music_mood: str = ""
    pacing: str = "moderate"

    # Quality scores (filled by QualityReviewer)
    quality_scores: dict[str, float] = field(default_factory=dict)
    approved: bool = False
    revision_notes: str = ""


class CreativeAgent:
    """Base class for all creative agents."""

    role: AgentRole = AgentRole.DIRECTOR

    def __init__(self) -> None:
        self._message_log: list[AgentMessage] = []

    async def process(self, brief: CreativeBrief) -> CreativeBrief:
        """Process the creative brief and return the updated version."""
        raise NotImplementedError

    def send_message(self, to: AgentRole, action: str, **payload) -> AgentMessage:
        msg = AgentMessage(
            sender=self.role,
            recipient=to,
            action=action,
            payload=payload,
        )
        self._message_log.append(msg)
        return msg

    @property
    def message_log(self) -> list[AgentMessage]:
        return list(self._message_log)
