"""Scheduler — automated content posting on a cron-like schedule.

Powered by the multi-agent creative system:
  1. Check queue first for pending items
  2. If queue is empty, Strategy Engine picks topic/category/type
  3. Creative Crew (6 agents) produces a quality-reviewed brief
  4. Content Pipeline generates media and publishes to Instagram
  5. Notifications sent via configured channels
"""

from __future__ import annotations

import asyncio
import json
import signal
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import structlog

from agents.crew import CreativeCrew
from config import settings
from pipeline.orchestrator import ContentPipeline, ContentRequest
from pipeline.queue import ContentQueue
from strategy.engine import StrategyEngine

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
        self.queue = ContentQueue()
        self._running = True
        self._posted_today: set[str] = set()
        self._stats = {"published": 0, "failed": 0, "skipped": 0}

    async def start(self) -> None:
        """Main loop — runs forever, posting at scheduled times."""
        logger.info(
            "scheduler.start",
            times=self.post_times,
            timezone=str(self.tz),
            queue_pending=self.queue.get_pending_count(),
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
            logger.info("scheduler.stats", **self._stats)

    async def _execute_post(self, time_slot: str) -> None:
        """Post content — from queue first, then strategy engine."""
        # 1. Try queue first
        queue_item = self.queue.dequeue()
        if queue_item:
            await self._post_from_queue(queue_item, time_slot)
            return

        # 2. Fall back to strategy engine
        await self._post_from_strategy(time_slot)

    async def _post_from_queue(self, item, time_slot: str) -> None:
        """Process a queued content item."""
        logger.info(
            "scheduler.queue_item",
            id=item.id,
            topic=item.topic,
            category=item.category,
        )

        crew = CreativeCrew()
        brief = await crew.produce(
            topic=item.topic,
            category=item.category,
            content_type=item.content_type,
            style_preset=item.style_preset,
            duration=item.duration,
        )

        request = ContentRequest(**crew.brief_to_content_request(brief))
        result = await self.pipeline.run(request)

        label = f"{item.category}:{item.topic[:30]}"

        if result.status == "published":
            self.queue.mark_published(item.id, result.media_id)
            self._stats["published"] += 1
            logger.info("scheduler.published", label=label, media_id=result.media_id)
            await self._notify(
                f"Published (queue): {label}\nMedia ID: {result.media_id}"
            )
        else:
            self.queue.mark_failed(item.id, result.error)
            self._stats["failed"] += 1
            logger.error("scheduler.failed", label=label, error=result.error)
            await self._notify(
                f"FAILED (queue): {label}\nError: {result.error}"
            )

        self._save_history_entry(label, item.content_type, result, time_slot)

    async def _post_from_strategy(self, time_slot: str) -> None:
        """Generate content based on strategy engine."""
        engine = StrategyEngine()
        day_slots = engine.plan_day(len(self.post_times))
        slot_index = self.post_times.index(time_slot) if time_slot in self.post_times else 0
        slot = day_slots[slot_index] if slot_index < len(day_slots) else day_slots[0]

        logger.info(
            "scheduler.strategy_post",
            topic=slot.topic,
            category=slot.category,
            time_slot=time_slot,
        )

        crew = CreativeCrew()
        brief = await crew.produce(
            topic=slot.topic,
            category=slot.category,
            content_type=slot.content_type,
            style_preset=slot.style_preset,
            duration=slot.duration,
        )

        request = ContentRequest(**crew.brief_to_content_request(brief))
        result = await self.pipeline.run(request)

        label = f"{slot.category}:{slot.topic[:30]}"

        if result.status == "published":
            self._stats["published"] += 1
            logger.info("scheduler.published", label=label, media_id=result.media_id)
            await self._notify(
                f"Published: {label}\nMedia ID: {result.media_id}"
            )
        else:
            self._stats["failed"] += 1
            logger.error("scheduler.failed", label=label, error=result.error)
            await self._notify(
                f"FAILED: {label}\nError: {result.error}"
            )

        self._save_history_entry(label, slot.content_type, result, time_slot)

    async def _notify(self, message: str) -> None:
        """Send notification via configured channel."""
        try:
            from notifications import NotificationManager
            manager = NotificationManager()
            await manager.send(message)
        except ImportError:
            pass  # Notifications not configured
        except Exception as exc:
            logger.warning("scheduler.notify_failed", error=str(exc))

    def _save_history_entry(
        self, label: str, content_type: str, result, time_slot: str
    ) -> None:
        """Append post result to history JSON file."""
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if HISTORY_FILE.exists():
            history = json.loads(HISTORY_FILE.read_text())

        history.append({
            "timestamp": datetime.now(self.tz).isoformat(),
            "time_slot": time_slot,
            "template": label,
            "content_type": content_type,
            "status": result.status,
            "media_id": result.media_id,
            "error": result.error,
            "request_id": result.request_id,
        })

        HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False))

    def _shutdown(self) -> None:
        logger.info("scheduler.shutdown", stats=self._stats)
        self._running = False
