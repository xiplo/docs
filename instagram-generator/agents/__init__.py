"""Multi-agent creative system for Instagram content generation.

Architecture:
    Director (Режиссёр) — orchestrates the entire creative process
      ├── Screenwriter (Сценарист) — writes scripts, captions, voiceover texts
      ├── PromptEngineer (Промт-инженер) — crafts optimized prompts for AI models
      ├── LightingArtist (Свет/Художник) — defines visual style, colors, mood
      ├── Editor (Монтажёр) — manages post-production, timing, transitions
      └── QualityReviewer (Контроль качества) — reviews and scores final output
"""

from .base import AgentRole, AgentMessage, CreativeAgent
from .director import DirectorAgent
from .screenwriter import ScreenwriterAgent
from .prompt_engineer import PromptEngineerAgent
from .lighting_artist import LightingArtistAgent
from .editor import EditorAgent
from .quality_reviewer import QualityReviewerAgent
from .crew import CreativeCrew

__all__ = [
    "AgentRole",
    "AgentMessage",
    "CreativeAgent",
    "DirectorAgent",
    "ScreenwriterAgent",
    "PromptEngineerAgent",
    "LightingArtistAgent",
    "EditorAgent",
    "QualityReviewerAgent",
    "CreativeCrew",
]
