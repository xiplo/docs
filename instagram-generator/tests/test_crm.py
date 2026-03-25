"""Tests for CRM modules."""

from unittest.mock import patch

import pytest


class TestAudienceManager:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "audience.json"
        with patch("crm.audience.AUDIENCE_FILE", f):
            yield f

    def test_default_segments(self):
        from crm.audience import AudienceManager
        mgr = AudienceManager()
        segments = mgr.get_all()
        assert len(segments) >= 4

    def test_get_for_content(self):
        from crm.audience import AudienceManager
        mgr = AudienceManager()
        matches = mgr.get_for_content("recipe", "reel")
        assert len(matches) >= 1

    def test_create_segment(self):
        from crm.audience import AudienceManager
        mgr = AudienceManager()
        s = mgr.create(name="Test Segment", age_range="30-45")
        assert s.id
        assert s.name == "Test Segment"

    def test_display(self):
        from crm.audience import AudienceManager
        mgr = AudienceManager()
        output = mgr.display()
        assert "Audience" in output


class TestEngagementTracker:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "engagement.json"
        with patch("crm.engagement.ENGAGEMENT_FILE", f):
            yield f

    def test_record_engagement(self):
        from crm.engagement import EngagementTracker
        tracker = EngagementTracker()
        entry = tracker.record(
            post_id="post1", platform="instagram",
            likes=100, comments=20, shares=5, impressions=5000,
            category="recipe",
        )
        assert entry.engagement_rate > 0

    def test_top_posts(self):
        from crm.engagement import EngagementTracker
        tracker = EngagementTracker()
        tracker.record(post_id="a", platform="instagram", likes=50, impressions=1000)
        tracker.record(post_id="b", platform="instagram", likes=200, impressions=3000)
        top = tracker.top_posts(1)
        assert top[0].post_id == "b"

    def test_display(self):
        from crm.engagement import EngagementTracker
        tracker = EngagementTracker()
        tracker.record(post_id="x", platform="instagram", likes=10, impressions=100)
        output = tracker.display()
        assert "Engagement" in output


class TestFollowerFunnel:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "funnel.json"
        with patch("crm.funnel.FUNNEL_FILE", f):
            yield f

    def test_record_snapshot(self):
        from crm.funnel import FollowerFunnel
        funnel = FollowerFunnel()
        snap = funnel.record(
            impressions=10000, reach=8000,
            profile_visits=500, new_followers=50,
            total_likes=300, total_comments=40,
        )
        assert snap.awareness_to_interest > 0

    def test_display(self):
        from crm.funnel import FollowerFunnel
        funnel = FollowerFunnel()
        funnel.record(impressions=5000, reach=4000, profile_visits=200)
        output = funnel.display()
        assert "Funnel" in output
        assert "Awareness" in output
