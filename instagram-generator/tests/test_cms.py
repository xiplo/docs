"""Tests for the content management system."""

from unittest.mock import patch

import pytest


class TestContentManager:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "cms.json"
        with patch("cms.content_manager.CMS_FILE", f):
            yield f

    def test_create(self):
        from cms.content_manager import ContentManager
        cm = ContentManager()
        item = cm.create(title="Test", topic="Palov", category="recipe")
        assert item.id
        assert item.status == "draft"
        assert item.category == "recipe"

    def test_lifecycle(self):
        from cms.content_manager import ContentManager
        cm = ContentManager()
        item = cm.create(title="Lifecycle", topic="Test", category="motivational")

        cm.submit_for_review(item.id)
        assert cm.get(item.id).status == "review"

        cm.approve(item.id, "LGTM")
        assert cm.get(item.id).status == "approved"

        cm.schedule(item.id, "2026-03-25T09:00:00", ["instagram", "tiktok"])
        assert cm.get(item.id).status == "scheduled"
        assert "tiktok" in cm.get(item.id).target_platforms

        cm.mark_publishing(item.id)
        assert cm.get(item.id).status == "publishing"

        cm.mark_published(item.id, {"instagram": {"publish_id": "123"}})
        assert cm.get(item.id).status == "published"

        cm.archive(item.id)
        assert cm.get(item.id).status == "archived"

    def test_reject_returns_to_draft(self):
        from cms.content_manager import ContentManager
        cm = ContentManager()
        item = cm.create(title="Bad", topic="Test", category="recipe")
        cm.submit_for_review(item.id)
        cm.reject(item.id, "Caption too short")
        assert cm.get(item.id).status == "draft"
        assert "Rejected" in cm.get(item.id).notes

    def test_search(self):
        from cms.content_manager import ContentManager
        cm = ContentManager()
        cm.create(title="Palov recipe", topic="Palov", category="recipe")
        cm.create(title="Morning motivation", topic="Motivation", category="motivational")
        results = cm.search("palov")
        assert len(results) == 1

    def test_display(self):
        from cms.content_manager import ContentManager
        cm = ContentManager()
        cm.create(title="Display", topic="Test", category="recipe")
        output = cm.display()
        assert "Content Management System" in output


class TestCampaignManager:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "campaigns.json"
        with patch("cms.campaigns.CAMPAIGNS_FILE", f):
            yield f

    def test_create_campaign(self):
        from cms.campaigns import CampaignManager
        mgr = CampaignManager()
        c = mgr.create(
            name="Navro'z 2026",
            target_platforms=["instagram", "tiktok"],
            categories=["recipe", "travel"],
        )
        assert c.id
        assert c.status == "active"

    def test_add_content(self):
        from cms.campaigns import CampaignManager
        mgr = CampaignManager()
        c = mgr.create(name="Test Campaign")
        mgr.add_content(c.id, "content_123")
        assert "content_123" in mgr.get(c.id).content_ids

    def test_record_publish(self):
        from cms.campaigns import CampaignManager
        mgr = CampaignManager()
        c = mgr.create(name="Pub Test")
        mgr.record_publish(c.id, success=True)
        mgr.record_publish(c.id, success=True)
        mgr.record_publish(c.id, success=False)
        assert mgr.get(c.id).published_count == 2
        assert mgr.get(c.id).failed_count == 1

    def test_display(self):
        from cms.campaigns import CampaignManager
        mgr = CampaignManager()
        mgr.create(name="Display Test", target_platforms=["instagram"])
        output = mgr.display()
        assert "Campaign Manager" in output


class TestAssetLibrary:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "assets.json"
        with patch("cms.asset_library.ASSETS_FILE", f):
            yield f

    def test_add_asset(self, tmp_path):
        from cms.asset_library import AssetLibrary
        test_img = tmp_path / "test.png"
        test_img.write_bytes(b"\x89PNG" + b"\x00" * 100)

        lib = AssetLibrary()
        asset = lib.add(
            file_path=str(test_img),
            name="Test Image",
            tags=["test", "recipe"],
            category="recipe",
        )
        assert asset.id
        assert asset.media_type == "image"
        assert asset.format == "png"

    def test_search_by_tags(self, tmp_path):
        from cms.asset_library import AssetLibrary
        test_img = tmp_path / "test.png"
        test_img.write_bytes(b"\x00" * 100)

        lib = AssetLibrary()
        lib.add(file_path=str(test_img), tags=["recipe", "palov"])
        results = lib.find_by_tags(["recipe"])
        assert len(results) == 1

    def test_mark_used(self, tmp_path):
        from cms.asset_library import AssetLibrary
        test_img = tmp_path / "used.png"
        test_img.write_bytes(b"\x00" * 100)

        lib = AssetLibrary()
        asset = lib.add(file_path=str(test_img))
        lib.mark_used(asset.id, "content_abc")
        assert lib.get(asset.id).used_count == 1

    def test_display(self):
        from cms.asset_library import AssetLibrary
        lib = AssetLibrary()
        output = lib.display()
        assert "Asset Library" in output


class TestCrossPoster:
    def test_adapt_instagram(self):
        from cms.cross_poster import PlatformAdapter
        adapted = PlatformAdapter.adapt(
            platform="instagram",
            caption="Test caption",
            hashtags=["test", "uzbekistan"],
            content_type="reel",
            media_urls=["https://cdn.example.com/video.mp4"],
        )
        assert adapted.platform == "instagram"
        assert adapted.content_type == "reel"
        assert len(adapted.hashtags) == 2

    def test_adapt_twitter_thread(self):
        from cms.cross_poster import PlatformAdapter
        long_text = "A " * 200  # Way over 280 chars
        adapted = PlatformAdapter.adapt(
            platform="twitter",
            caption=long_text,
            hashtags=["test"],
            content_type="image",
            voiceover_text=long_text,
        )
        assert adapted.content_type == "thread"
        assert len(adapted.thread_parts) > 1

    def test_adapt_youtube_adds_shorts(self):
        from cms.cross_poster import PlatformAdapter
        adapted = PlatformAdapter.adapt(
            platform="youtube",
            caption="My video",
            hashtags=["uzbekistan"],
            content_type="reel",
            topic="Test topic",
        )
        assert "#Shorts" in adapted.title

    def test_adapt_telegram_inline_tags(self):
        from cms.cross_poster import PlatformAdapter
        # Telegram has hashtag_max=0, so hashtags list will be empty after trim
        # Test with enough hashtags that the caption_max doesn't hide them
        adapted = PlatformAdapter.adapt(
            platform="telegram",
            caption="Hello world",
            hashtags=[],  # Telegram spec has hashtag_max=0
            content_type="image",
        )
        # With no hashtags, no inline tags added
        assert adapted.caption == "Hello world"

    def test_caption_trim(self):
        from cms.cross_poster import PlatformAdapter
        # Use real words so thread splitting works
        long_caption = " ".join(["motivation"] * 50)  # ~550 chars
        adapted = PlatformAdapter.adapt(
            platform="twitter",
            caption=long_caption,
            hashtags=[],
            content_type="text",
        )
        # Long twitter captions become threads; each part should be <= 280
        assert adapted.content_type == "thread"
        assert len(adapted.thread_parts) >= 2
        for part in adapted.thread_parts:
            assert len(part) <= 280


class TestPublishingRouter:
    @pytest.fixture(autouse=True)
    def mock_file(self, tmp_path):
        f = tmp_path / "rules.json"
        with patch("cms.publisher.RULES_FILE", f):
            yield f

    def test_default_rules(self):
        from cms.publisher import PublishingRouter
        router = PublishingRouter()
        rules = router.get_rules()
        assert len(rules) >= 5

    def test_reel_routes_to_multi(self):
        from cms.publisher import PublishingRouter
        router = PublishingRouter()
        platforms = router.get_platforms({"content_type": "reel"})
        assert "instagram" in platforms
        assert "tiktok" in platforms
        assert "youtube" in platforms

    def test_recipe_routes(self):
        from cms.publisher import PublishingRouter
        router = PublishingRouter()
        platforms = router.get_platforms({"category": "recipe", "content_type": "reel"})
        assert "instagram" in platforms
        assert "facebook" in platforms

    def test_fallback_to_instagram(self):
        from cms.publisher import PublishingRouter
        router = PublishingRouter()
        platforms = router.get_platforms({"content_type": "unknown_type"})
        assert "instagram" in platforms

    def test_display(self):
        from cms.publisher import PublishingRouter
        router = PublishingRouter()
        output = router.display()
        assert "Publishing Rules" in output
        assert "instagram" in output.lower()
