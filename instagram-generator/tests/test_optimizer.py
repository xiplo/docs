"""Tests for engagement optimizer."""

import json
from unittest.mock import patch

import pytest

from strategy.optimizer import EngagementOptimizer, DEFAULT_BEST_TIMES


class TestEngagementOptimizer:
    def test_optimize_defaults_when_no_history(self):
        with patch.object(EngagementOptimizer, "_load_history", return_value=[]):
            results = EngagementOptimizer.optimize("instagram")
            assert len(results) == 1
            assert results[0].platform == "instagram"
            assert results[0].confidence == "default"
            assert len(results[0].best_times) > 0

    def test_optimize_all_platforms(self):
        with patch.object(EngagementOptimizer, "_load_history", return_value=[]):
            results = EngagementOptimizer.optimize()
            platforms = {r.platform for r in results}
            assert "instagram" in platforms
            assert "twitter" in platforms
            assert "tiktok" in platforms

    def test_get_best_time(self):
        with patch.object(EngagementOptimizer, "_load_history", return_value=[]):
            time = EngagementOptimizer.get_best_time("instagram")
            assert ":" in time

    def test_get_schedule(self):
        with patch.object(EngagementOptimizer, "_load_history", return_value=[]):
            schedule = EngagementOptimizer.get_schedule(["instagram", "tiktok"], posts_per_day=2)
            assert "instagram" in schedule
            assert len(schedule["instagram"]) <= 2

    def test_display(self):
        with patch.object(EngagementOptimizer, "_load_history", return_value=[]):
            output = EngagementOptimizer.display()
            assert "Optimizer" in output
            assert "INSTAGRAM" in output

    def test_analyze_with_history(self):
        history = [
            {"timestamp": "2026-03-20T09:00:00", "status": "published", "platform": "instagram"},
            {"timestamp": "2026-03-20T09:00:00", "status": "published", "platform": "instagram"},
            {"timestamp": "2026-03-20T13:00:00", "status": "published", "platform": "instagram"},
            {"timestamp": "2026-03-20T18:00:00", "status": "failed", "platform": "instagram"},
        ] * 5  # 20 posts

        with patch.object(EngagementOptimizer, "_load_history", return_value=history):
            results = EngagementOptimizer.optimize("instagram")
            assert results[0].confidence == "medium"

    def test_default_best_times_complete(self):
        for platform in ["instagram", "twitter", "tiktok", "youtube", "facebook", "telegram", "linkedin"]:
            assert platform in DEFAULT_BEST_TIMES
            assert len(DEFAULT_BEST_TIMES[platform]) >= 3
