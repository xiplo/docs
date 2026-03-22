"""Tests for content queue."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.queue import ContentQueue, QueueItem


@pytest.fixture(autouse=True)
def mock_queue_file(tmp_path):
    """Redirect queue storage to temp directory."""
    queue_file = tmp_path / "test_queue.json"
    with patch("pipeline.queue.QUEUE_FILE", queue_file):
        yield queue_file


class TestContentQueue:
    def test_enqueue(self):
        q = ContentQueue()
        item = q.enqueue("Palov retsepti", "recipe", "reel")
        assert item.topic == "Palov retsepti"
        assert item.category == "recipe"
        assert item.status == "queued"
        assert item.id  # Non-empty

    def test_dequeue_highest_priority(self):
        q = ContentQueue()
        q.enqueue("Low", "recipe", priority=1)
        q.enqueue("High", "motivational", priority=10)
        q.enqueue("Medium", "travel", priority=5)

        item = q.dequeue()
        assert item is not None
        assert item.topic == "High"
        assert item.status == "processing"

    def test_dequeue_empty(self):
        q = ContentQueue()
        assert q.dequeue() is None

    def test_deduplication(self):
        q = ContentQueue()
        item1 = q.enqueue("Same topic", "recipe")
        item2 = q.enqueue("Same topic", "recipe")
        assert item1.id == item2.id  # Same item returned
        assert q.get_pending_count() == 1

    def test_mark_published(self):
        q = ContentQueue()
        item = q.enqueue("Test", "motivational")
        q.mark_published(item.id, "media_123")

        # Reload and check
        q2 = ContentQueue()
        found = q2._find(item.id)
        assert found is not None
        assert found.status == "published"
        assert found.media_id == "media_123"

    def test_mark_failed_retries(self):
        q = ContentQueue()
        item = q.enqueue("Test", "motivational")
        q.mark_failed(item.id, "timeout")

        found = q._find(item.id)
        assert found is not None
        assert found.status == "queued"  # Re-queued for retry
        assert found.retry_count == 1

    def test_mark_failed_max_retries(self):
        q = ContentQueue()
        item = q.enqueue("Test", "motivational")
        for i in range(3):
            q.mark_failed(item.id, f"error_{i}")

        found = q._find(item.id)
        assert found is not None
        assert found.status == "failed"
        assert found.retry_count == 3

    def test_cancel(self):
        q = ContentQueue()
        item = q.enqueue("Cancel me", "recipe")
        assert q.cancel(item.id) is True

        found = q._find(item.id)
        assert found.status == "cancelled"

    def test_stats(self):
        q = ContentQueue()
        q.enqueue("A", "recipe")
        q.enqueue("B", "travel")
        item = q.enqueue("C", "motivational")
        q.mark_published(item.id)

        stats = q.get_stats()
        assert stats["queued"] == 2
        assert stats["published"] == 1

    def test_persistence(self):
        q1 = ContentQueue()
        q1.enqueue("Persistent", "recipe")

        q2 = ContentQueue()
        assert q2.get_pending_count() == 1

    def test_display(self):
        q = ContentQueue()
        q.enqueue("Display test", "motivational")
        output = q.display()
        assert "Content Queue" in output
        assert "Display test" in output
