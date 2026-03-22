"""Scheduler — automated content posting on a cron-like schedule.

Now powered by the multi-agent creative system:
  1. Strategy Engine picks topic/category/type
  2. Creative Crew (6 agents) produces a quality-reviewed brief
  3. Content Pipeline generates media and publishes to Instagram
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

from agents.crew import CreativeCrew
from config import settings
from pipeline.orchestrator import ContentPipeline, ContentRequest
from strategy.engine import StrategyEngine
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
        """Use agent system to produce content, then publish."""
        # Strategy engine picks what to post
        engine = StrategyEngine()
        day_slots = engine.plan_day(len(self.post_times))
        slot_index = self.post_times.index(time_slot) if time_slot in self.post_times else 0
        slot = day_slots[slot_index] if slot_index < len(day_slots) else day_slots[0]

        logger.info(
            "scheduler.posting",
            topic=slot.topic,
            category=slot.category,
            time_slot=time_slot,
        )

        # Agent crew produces a creative brief
        crew = CreativeCrew()
        brief = await crew.produce(
            topic=slot.topic,
            category=slot.category,
            content_type=slot.content_type,
            style_preset=slot.style_preset,
            duration=slot.duration,
        )

        # Convert brief to pipeline request
        request_data = crew.brief_to_content_request(brief)
        request = ContentRequest(**request_data)

        result = await self.pipeline.run(request)

        # Build a template-like object for history
        template = type("Slot", (), {
            "name": f"{slot.category}:{slot.topic[:30]}",
            "content_type": slot.content_type,
        })()

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
