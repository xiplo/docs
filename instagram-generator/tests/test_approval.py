"""Tests for content approval workflow."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pipeline.approval import ApprovalWorkflow, ReviewItem


@pytest.fixture(autouse=True)
def mock_review_file(tmp_path):
    review_file = tmp_path / "test_review.json"
    with patch("pipeline.approval.REVIEW_FILE", review_file):
        yield review_file


class TestApprovalWorkflow:
    def test_submit_for_review(self):
        wf = ApprovalWorkflow()
        item = wf.submit_for_review(
            request_id="test123",
            topic="Palov",
            category="recipe",
            content_type="reel",
            caption="Palov tayyorlash!",
            hashtags=["palov", "taom"],
            quality_scores={"visual": 8.0, "script": 7.5},
        )
        assert item.id == "test123"
        assert item.status == "pending"

    def test_approve(self):
        wf = ApprovalWorkflow()
        wf.submit_for_review(
            request_id="approve_me",
            topic="Test",
            category="motivational",
            content_type="image",
            caption="Test caption",
            hashtags=[],
        )
        result = wf.approve("approve_me", "Looks great!")
        assert result is not None
        assert result.status == "approved"
        assert result.reviewer_notes == "Looks great!"

    def test_reject(self):
        wf = ApprovalWorkflow()
        wf.submit_for_review(
            request_id="reject_me",
            topic="Bad content",
            category="recipe",
            content_type="reel",
            caption="Bad",
            hashtags=[],
        )
        result = wf.reject("reject_me", "Caption too short")
        assert result is not None
        assert result.status == "rejected"

    def test_approve_nonexistent(self):
        wf = ApprovalWorkflow()
        assert wf.approve("nonexistent") is None

    def test_get_pending(self):
        wf = ApprovalWorkflow()
        wf.submit_for_review("a", "T1", "recipe", "reel", "C1", [])
        wf.submit_for_review("b", "T2", "travel", "image", "C2", [])
        wf.approve("a")

        pending = wf.get_pending()
        assert len(pending) == 1
        assert pending[0].id == "b"

    def test_display(self):
        wf = ApprovalWorkflow()
        wf.submit_for_review("x", "Display test", "motivational", "reel", "Caption", [])
        output = wf.display()
        assert "Review Queue" in output
        assert "Display test" in output

    def test_persistence(self):
        wf1 = ApprovalWorkflow()
        wf1.submit_for_review("persist", "Test", "recipe", "reel", "C", [])

        wf2 = ApprovalWorkflow()
        assert len(wf2.get_pending()) == 1
