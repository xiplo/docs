"""Tests for trending topics engine."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from strategy.trends import TrendEngine, TrendingTopic


class TestTrendEngine:
    def test_get_current_trends(self):
        trends = TrendEngine.get_current_trends(limit=10)
        assert isinstance(trends, list)
        # Should always return something (monthly trends exist for every month)
        assert len(trends) > 0

    def test_trends_sorted_by_relevance(self):
        trends = TrendEngine.get_current_trends(limit=10)
        for i in range(len(trends) - 1):
            assert trends[i].relevance_score >= trends[i + 1].relevance_score

    def test_get_trending_hashtags(self):
        tags = TrendEngine.get_trending_hashtags()
        assert isinstance(tags, list)
        assert len(tags) > 0
        # Should include evergreen tags
        assert "uzbekistan" in tags

    def test_get_trending_hashtags_by_category(self):
        tags = TrendEngine.get_trending_hashtags(category="recipe")
        assert isinstance(tags, list)

    def test_suggest_content_for_trend(self):
        trend = TrendingTopic(
            name="Test Trend",
            category="motivational",
            relevance_score=0.9,
            hashtags=["test"],
            suggested_hook="Hook!",
        )
        suggestion = TrendEngine.suggest_content_for_trend(trend)
        assert suggestion["topic"] == "Test Trend"
        assert suggestion["category"] == "motivational"
        assert suggestion["content_type"] == "reel"
        assert suggestion["priority"] == 9

    def test_display_trends(self):
        output = TrendEngine.display_trends()
        assert "Trending Topics" in output

    def test_navriz_detected_in_march(self):
        with patch("strategy.trends.date") as mock_date:
            mock_date.today.return_value = date(2026, 3, 21)
            mock_date.side_effect = lambda *a, **k: date(*a, **k)
            trends = TrendEngine.get_current_trends(limit=20)
            names = [t.name for t in trends]
            # March should have Navro'z-related trends
            assert any("Navro" in n or "Bahor" in n for n in names)
