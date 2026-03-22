"""Batch processing — generate multiple content pieces in one run.

Use cases:
  - Pre-generate a week of content overnight
  - Process entire queue in one pass
  - Bulk generate from calendar plan
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime

import structlog

from agents.crew import CreativeCrew
from config import settings
from pipeline.orchestrator import ContentPipeline, ContentRequest, ContentResult
from pipeline.queue import ContentQueue

logger = structlog.get_logger(__name__)


@dataclass
class BatchResult:
    """Results of a batch processing run."""

    total: int = 0
    published: int = 0
    failed: int = 0
    blocked: int = 0
    skipped: int = 0
    results: list[ContentResult] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    @property
    def success_rate(self) -> float:
        return self.published / self.total * 100 if self.total else 0

    def display(self) -> str:
        lines = [
            "=" * 55,
            "  Batch Processing Results",
            "=" * 55,
            f"  Total:     {self.total}",
            f"  Published: {self.published}",
            f"  Failed:    {self.failed}",
            f"  Blocked:   {self.blocked}",
            f"  Skipped:   {self.skipped}",
            f"  Success:   {self.success_rate:.0f}%",
            f"  Duration:  {self.started_at[:19]} → {self.finished_at[:19]}",
            "=" * 55,
        ]
        return "\n".join(lines)


class BatchProcessor:
    """Process multiple content items in sequence or parallel."""

    def __init__(self, concurrency: int = 1) -> None:
        self.concurrency = concurrency
        self.crew = CreativeCrew()

    async def process_queue(self, limit: int = 10) -> BatchResult:
        """Process up to `limit` items from the content queue."""
        queue = ContentQueue()
        batch = BatchResult(started_at=datetime.now().isoformat())

        items = []
        for _ in range(limit):
            item = queue.dequeue()
            if item is None:
                break
            items.append(item)

        batch.total = len(items)
        logger.info("batch.start", items=batch.total, concurrency=self.concurrency)

        if self.concurrency <= 1:
            # Sequential processing
            pipeline = ContentPipeline()
            try:
                for item in items:
                    result = await self._process_item(pipeline, item)
                    batch.results.append(result)
                    self._update_counts(batch, result)
                    self._update_queue(queue, item, result)
            finally:
                await pipeline.close()
        else:
            # Limited parallel processing
            semaphore = asyncio.Semaphore(self.concurrency)

            async def process_with_semaphore(item):
                async with semaphore:
                    pipeline = ContentPipeline()
                    try:
                        return await self._process_item(pipeline, item)
                    finally:
                        await pipeline.close()

            tasks = [process_with_semaphore(item) for item in items]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for item, result in zip(items, results):
                if isinstance(result, Exception):
                    error_result = ContentResult(
                        request_id=item.id,
                        content_type=item.content_type,
                        status="failed",
                        error=str(result),
                    )
                    batch.results.append(error_result)
                    batch.failed += 1
                    queue.mark_failed(item.id, str(result))
                else:
                    batch.results.append(result)
                    self._update_counts(batch, result)
                    self._update_queue(queue, item, result)

        batch.finished_at = datetime.now().isoformat()
        logger.info(
            "batch.complete",
            total=batch.total,
            published=batch.published,
            failed=batch.failed,
        )
        return batch

    async def process_topics(
        self,
        topics: list[dict],
    ) -> BatchResult:
        """Process a list of topic dicts [{topic, category, content_type, ...}]."""
        batch = BatchResult(
            total=len(topics),
            started_at=datetime.now().isoformat(),
        )

        pipeline = ContentPipeline()
        try:
            for topic_config in topics:
                brief = await self.crew.produce(
                    topic=topic_config.get("topic", ""),
                    category=topic_config.get("category", "motivational"),
                    content_type=topic_config.get("content_type", "reel"),
                    style_preset=topic_config.get("style_preset", "photorealistic"),
                    duration=topic_config.get("duration", "5"),
                )

                request = ContentRequest(**self.crew.brief_to_content_request(brief))
                result = await pipeline.run(request)
                batch.results.append(result)
                self._update_counts(batch, result)

                logger.info(
                    "batch.item",
                    topic=topic_config.get("topic", ""),
                    status=result.status,
                )
        finally:
            await pipeline.close()

        batch.finished_at = datetime.now().isoformat()
        return batch

    async def _process_item(
        self, pipeline: ContentPipeline, item
    ) -> ContentResult:
        """Generate and publish a single queue item."""
        brief = await self.crew.produce(
            topic=item.topic,
            category=item.category,
            content_type=item.content_type,
            style_preset=item.style_preset,
            duration=item.duration,
        )
        request = ContentRequest(**self.crew.brief_to_content_request(brief))
        return await pipeline.run(request)

    @staticmethod
    def _update_counts(batch: BatchResult, result: ContentResult) -> None:
        if result.status == "published":
            batch.published += 1
        elif result.status == "blocked":
            batch.blocked += 1
        else:
            batch.failed += 1

    @staticmethod
    def _update_queue(queue: ContentQueue, item, result: ContentResult) -> None:
        if result.status == "published":
            queue.mark_published(item.id, result.media_id)
        else:
            queue.mark_failed(item.id, result.error)
