"""Tests for strategy engine and content calendar."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from strategy.engine import StrategyEngine


class TestStrategyEngine:
    def test_plan_day(self):
        engine = StrategyEngine()
        slots = engine.plan_day(posts_per_day=3)
        assert len(slots) == 3
        for slot in slots:
            assert slot.topic
            assert slot.category
            assert slot.content_type

    def test_plan_week(self):
        engine = StrategyEngine()
        slots = engine.plan_week(posts_per_day=2)
        assert len(slots) == 14  # 7 days * 2 posts

    def test_no_topic_collision_in_day(self):
        engine = StrategyEngine()
        slots = engine.plan_day(posts_per_day=3)
        topics = [s.topic for s in slots]
        assert len(topics) == len(set(topics)), "Topics should not repeat in a day"

    def test_slots_have_valid_content_types(self):
        engine = StrategyEngine()
        valid = {"reel", "image", "carousel", "story"}
        slots = engine.plan_day()
        for slot in slots:
            assert slot.content_type in valid
