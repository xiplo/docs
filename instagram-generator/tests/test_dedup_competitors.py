"""Tests for deduplication and competitor tracking."""

from unittest.mock import patch

import pytest

from skills.deduplication import DuplicateDetector


class TestDuplicateDetector:
    def test_no_history_no_duplicate(self):
        with patch.object(DuplicateDetector, "_load_recent", return_value=[]):
            is_dup, reason = DuplicateDetector.is_duplicate("Palov recipe")
            assert is_dup is False

    def test_exact_match_detected(self):
        history = [
            {"topic": "Palov recipe", "category": "recipe", "timestamp": "2026-03-20T12:00:00"},
        ]
        with patch.object(DuplicateDetector, "_load_recent", return_value=history):
            is_dup, reason = DuplicateDetector.is_duplicate("Palov recipe", category="recipe")
            assert is_dup is True
            assert "Exact" in reason

    def test_fuzzy_match_detected(self):
        history = [
            {"topic": "Traditional palov recipe for family", "category": "recipe", "timestamp": "2026-03-20"},
        ]
        with patch.object(DuplicateDetector, "_load_recent", return_value=history):
            is_dup, reason = DuplicateDetector.is_duplicate("Palov recipe for the family", threshold=0.5)
            assert is_dup is True

    def test_different_content_passes(self):
        history = [
            {"topic": "Morning motivation", "category": "motivational", "timestamp": "2026-03-20"},
        ]
        with patch.object(DuplicateDetector, "_load_recent", return_value=history):
            is_dup, reason = DuplicateDetector.is_duplicate("Palov recipe")
            assert is_dup is False

    def test_find_similar(self):
        history = [
            {"topic": "Palov recipe traditional", "category": "recipe", "timestamp": "2026-03-20"},
            {"topic": "Morning run tips", "category": "fitness", "timestamp": "2026-03-19"},
        ]
        with patch.object(DuplicateDetector, "_load_recent", return_value=history):
            similar = DuplicateDetector.find_similar("Palov cooking recipe")
            assert len(similar) >= 1
            assert similar[0]["similarity"] > 0.3

    def test_display(self):
        with patch.object(DuplicateDetector, "_load_recent", return_value=[]):
            output = DuplicateDetector.display("test topic")
            assert "Duplicate" in output

    def test_token_similarity(self):
        sim = DuplicateDetector._token_similarity("hello world test", "hello world demo")
        assert 0.3 < sim < 0.8

    def test_ngram_similarity(self):
        sim = DuplicateDetector._ngram_similarity("hello world", "hello world")
        assert sim == 1.0


class TestCompetitorTracker:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "competitors.json"
        with patch("strategy.competitors.COMPETITORS_FILE", f):
            yield f

    def test_add_competitor(self):
        from strategy.competitors import CompetitorTracker
        tracker = CompetitorTracker()
        comp = tracker.add(name="Rival Brand", platform="instagram", handle="@rival")
        assert comp.id
        assert comp.name == "Rival Brand"

    def test_update_metrics(self):
        from strategy.competitors import CompetitorTracker
        tracker = CompetitorTracker()
        comp = tracker.add(name="Test Comp")
        tracker.update_metrics(comp.id, followers=10000, avg_likes=500)
        updated = tracker.get(comp.id)
        assert updated.followers == 10000
        assert len(updated.history) == 1

    def test_compare_display(self):
        from strategy.competitors import CompetitorTracker
        tracker = CompetitorTracker()
        tracker.add(name="Comp A", followers=5000, avg_likes=200)
        tracker.add(name="Comp B", followers=15000, avg_likes=800)
        output = tracker.compare()
        assert "Competitor" in output
        assert "Comp B" in output
