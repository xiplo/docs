"""Scheduler — automated content posting on a cron-like schedule.

Reads the schedule from CONTENT_SCHEDULE or uses defaults.
Selects templates in rotation, generates content, and posts to Instagram.
"""

from __future__ import annotations

import asyncio
import json
import random
import signal
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import structlog

from config import settings
from pipeline.orchestrator import ContentPipeline, ContentRequest
from templates.prompts import TEMPLATES, ContentTemplate

logger = structlog.get_logger(__name__)

# Default posting times (Tashkent time)
DEFAULT_POST_TIMES = ["09:00", "13:00", "18:00"]

HISTORY_FILE = Path(settings.content_output_dir) / "post_history.json"


class ContentScheduler:
    """Schedules and executes content generation + posting."""

    def __init__(
        self,
        post_times: list[str] | None = None,
        timezone: str | None = None,
    ) -> None:
        self.post_times = post_times or DEFAULT_POST_TIMES
        self.tz = ZoneInfo(timezone or settings.timezone)
        self.pipeline = ContentPipeline()
        self._running = True
        self._posted_today: set[str] = set()
        self._template_index = 0

    async def start(self) -> None:
        """Main loop — runs forever, posting at scheduled times."""
        logger.info(
            "scheduler.start",
            times=self.post_times,
            timezone=str(self.tz),
        )

        # Handle graceful shutdown
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._shutdown)

        try:
            while self._running:
                now = datetime.now(self.tz)
                current_time = now.strftime("%H:%M")
                today = now.strftime("%Y-%m-%d")

                # Reset daily tracking at midnight
                if not self._posted_today or today not in str(self._posted_today):
                    self._posted_today.clear()

                # Check if it's time to post
                for post_time in self.post_times:
                    slot_key = f"{today}_{post_time}"
                    if current_time == post_time and slot_key not in self._posted_today:
                        self._posted_today.add(slot_key)
                        await self._execute_post(post_time)

                await asyncio.sleep(30)  # Check every 30 seconds
        finally:
            await self.pipeline.close()

    async def _execute_post(self, time_slot: str) -> None:
        """Pick a template, generate content, and post."""
        template = self._next_template()
        logger.info(
            "scheduler.posting",
            template=template.name,
            time_slot=time_slot,
        )

        request = ContentRequest(
            content_type=template.content_type,
            image_prompt=template.image_prompt,
            caption=template.caption,
            voiceover_text=template.voiceover_text,
            image_style=template.image_style,
            video_duration=template.video_duration,
            subtitle_text=template.subtitle_text,
            carousel_prompts=template.carousel_prompts,
            hashtags=template.hashtags,
        )

        result = await self.pipeline.run(request)
        self._save_history(template, result, time_slot)

        if result.status == "published":
            logger.info(
                "scheduler.published",
                template=template.name,
                media_id=result.media_id,
            )
        else:
            logger.error(
                "scheduler.failed",
                template=template.name,
                error=result.error,
            )

    def _next_template(self) -> ContentTemplate:
        """Rotate through templates, with some randomization."""
        # 70% rotation, 30% random pick for variety
        if random.random() < 0.3:
            return random.choice(TEMPLATES)

        template = TEMPLATES[self._template_index % len(TEMPLATES)]
        self._template_index += 1
        return template

    def _save_history(self, template, result, time_slot: str) -> None:
        """Append post result to history JSON file."""
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if HISTORY_FILE.exists():
            history = json.loads(HISTORY_FILE.read_text())

        history.append({
            "timestamp": datetime.now(self.tz).isoformat(),
            "time_slot": time_slot,
            "template": template.name,
            "content_type": template.content_type,
            "status": result.status,
            "media_id": result.media_id,
            "error": result.error,
            "request_id": result.request_id,
        })

        HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False))

    def _shutdown(self) -> None:
        logger.info("scheduler.shutdown")
        self._running = False
