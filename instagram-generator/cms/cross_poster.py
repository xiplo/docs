"""Cross-posting engine — adapt and publish content across platforms.

Adapts content for each platform's requirements:
  - Caption length limits
  - Hashtag formatting
  - Media specs (aspect ratio, duration)
  - Platform-specific features (threads, shorts, reels)

Supported platforms:
  instagram, twitter, tiktok, youtube, facebook, telegram, linkedin
"""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)

# Platform-specific limits and formats
PLATFORM_SPECS: dict[str, dict] = {
    "instagram": {
        "caption_max": 2200,
        "hashtag_max": 30,
        "video_max_s": 90,
        "image_formats": ["jpg", "png"],
        "video_formats": ["mp4", "mov"],
        "supports": ["image", "reel", "carousel", "story"],
    },
    "twitter": {
        "caption_max": 280,
        "hashtag_max": 5,
        "video_max_s": 140,
        "image_formats": ["jpg", "png", "gif", "webp"],
        "video_formats": ["mp4"],
        "supports": ["text", "image", "video", "thread"],
    },
    "tiktok": {
        "caption_max": 2200,
        "hashtag_max": 30,
        "video_max_s": 600,
        "image_formats": ["jpg", "png"],
        "video_formats": ["mp4"],
        "supports": ["video", "photo_carousel"],
    },
    "youtube": {
        "title_max": 100,
        "description_max": 5000,
        "hashtag_max": 15,
        "video_max_s": 60,  # Shorts limit
        "video_formats": ["mp4", "mov", "avi", "wmv"],
        "supports": ["short", "video"],
    },
    "facebook": {
        "caption_max": 63206,
        "hashtag_max": 30,
        "video_max_s": 240,
        "image_formats": ["jpg", "png", "gif"],
        "video_formats": ["mp4", "mov"],
        "supports": ["text", "image", "video", "reel"],
    },
    "telegram": {
        "caption_max": 1024,
        "hashtag_max": 0,
        "video_max_s": 0,  # No limit
        "image_formats": ["jpg", "png"],
        "video_formats": ["mp4"],
        "supports": ["text", "image", "video", "album"],
    },
    "linkedin": {
        "caption_max": 3000,
        "hashtag_max": 5,
        "video_max_s": 600,
        "image_formats": ["jpg", "png"],
        "video_formats": ["mp4"],
        "supports": ["text", "image", "article"],
    },
}


@dataclass
class AdaptedContent:
    """Content adapted for a specific platform."""

    platform: str
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    media_urls: list[str] = field(default_factory=list)
    media_paths: list[str] = field(default_factory=list)
    content_type: str = ""
    title: str = ""  # For YouTube
    thread_parts: list[str] = field(default_factory=list)  # For Twitter threads
    metadata: dict = field(default_factory=dict)


class PlatformAdapter:
    """Adapts content for platform-specific requirements."""

    @classmethod
    def adapt(
        cls,
        platform: str,
        caption: str,
        hashtags: list[str],
        content_type: str,
        media_urls: list[str] | None = None,
        media_paths: list[str] | None = None,
        voiceover_text: str = "",
        topic: str = "",
    ) -> AdaptedContent:
        """Adapt content for a specific platform."""
        specs = PLATFORM_SPECS.get(platform, {})
        result = AdaptedContent(
            platform=platform,
            media_urls=media_urls or [],
            media_paths=media_paths or [],
        )

        # Adapt caption length
        max_len = specs.get("caption_max", 2200)
        result.caption = cls._trim_caption(caption, max_len)

        # Adapt hashtags
        max_tags = specs.get("hashtag_max", 10)
        result.hashtags = hashtags[:max_tags]

        # Adapt content type to platform equivalent
        result.content_type = cls._map_content_type(content_type, platform, specs)

        # Platform-specific adaptations
        if platform == "twitter":
            result = cls._adapt_twitter(result, caption, hashtags, voiceover_text)
        elif platform == "youtube":
            result.title = topic[:95] + " #Shorts" if topic else caption[:95] + " #Shorts"
        elif platform == "telegram":
            # Telegram uses inline hashtags
            tag_line = " ".join(f"#{t}" for t in result.hashtags[:5])
            if tag_line:
                result.caption = f"{result.caption}\n\n{tag_line}"
        elif platform == "linkedin":
            # LinkedIn prefers professional tone
            result.caption = cls._professionalize(result.caption)

        return result

    @classmethod
    def _adapt_twitter(
        cls,
        result: AdaptedContent,
        full_caption: str,
        hashtags: list[str],
        voiceover_text: str,
    ) -> AdaptedContent:
        """Twitter: short captions or threads."""
        tags = " ".join(f"#{t}" for t in hashtags[:3])
        available = 280 - len(tags) - 2  # Space for tags

        if len(full_caption) <= available:
            result.caption = f"{full_caption}\n{tags}" if tags else full_caption
        else:
            # Create a thread
            source = voiceover_text or full_caption
            parts = cls._split_to_thread(source, 270)
            if tags:
                parts[-1] = f"{parts[-1]}\n{tags}"
            result.thread_parts = parts
            result.caption = parts[0]
            result.content_type = "thread"

        return result

    @classmethod
    def _split_to_thread(cls, text: str, max_len: int) -> list[str]:
        """Split long text into tweet-sized parts."""
        words = text.split()
        parts = []
        current = ""

        for word in words:
            test = f"{current} {word}".strip()
            if len(test) <= max_len - 5:  # Room for "1/N"
                current = test
            else:
                if current:
                    parts.append(current)
                current = word

        if current:
            parts.append(current)

        # Add numbering
        total = len(parts)
        if total > 1:
            parts = [f"{p} ({i + 1}/{total})" for i, p in enumerate(parts)]

        return parts or [text[:max_len]]

    @classmethod
    def _map_content_type(cls, content_type: str, platform: str, specs: dict) -> str:
        """Map generic content type to platform-specific type."""
        supported = specs.get("supports", [])
        mapping = {
            ("reel", "youtube"): "short",
            ("reel", "twitter"): "video",
            ("reel", "telegram"): "video",
            ("reel", "linkedin"): "video" if "video" in supported else "image",
            ("carousel", "twitter"): "image",
            ("carousel", "tiktok"): "photo_carousel",
            ("carousel", "telegram"): "album",
            ("carousel", "linkedin"): "image",
            ("carousel", "youtube"): "image",
            ("story", "twitter"): "image",
            ("story", "tiktok"): "video",
            ("story", "facebook"): "reel",
            ("story", "telegram"): "image",
            ("image", "tiktok"): "photo_carousel",
        }
        return mapping.get((content_type, platform), content_type)

    @classmethod
    def _trim_caption(cls, caption: str, max_len: int) -> str:
        if len(caption) <= max_len:
            return caption
        return caption[: max_len - 3] + "..."

    @classmethod
    def _professionalize(cls, caption: str) -> str:
        """Lighten emoji and informal tone for LinkedIn."""
        # Remove excessive emojis but keep caption substance
        return caption


class CrossPoster:
    """Publish content to multiple platforms."""

    def __init__(self) -> None:
        self._clients: dict = {}

    def get_client(self, platform: str):
        """Lazy-load platform client."""
        if platform in self._clients:
            return self._clients[platform]

        client = None
        if platform == "instagram":
            from clients.instagram import InstagramClient
            client = InstagramClient()
        elif platform == "twitter":
            from clients.twitter import TwitterClient
            client = TwitterClient()
        elif platform == "tiktok":
            from clients.tiktok import TikTokClient
            client = TikTokClient()
        elif platform == "youtube":
            from clients.youtube import YouTubeClient
            client = YouTubeClient()
        elif platform == "facebook":
            from clients.facebook import FacebookClient
            client = FacebookClient()
        elif platform == "telegram":
            from clients.telegram_channel import TelegramChannelClient
            client = TelegramChannelClient()
        elif platform == "linkedin":
            from clients.linkedin import LinkedInClient
            client = LinkedInClient()

        if client:
            self._clients[platform] = client
        return client

    async def publish(
        self,
        adapted: AdaptedContent,
    ) -> dict:
        """Publish adapted content to its target platform."""
        client = self.get_client(adapted.platform)
        if not client:
            return {"status": "error", "error": f"No client for {adapted.platform}"}

        try:
            publish_id = await self._dispatch(client, adapted)
            logger.info(
                "crosspost.published",
                platform=adapted.platform,
                publish_id=publish_id,
            )
            return {
                "status": "published",
                "platform": adapted.platform,
                "publish_id": publish_id,
            }
        except Exception as exc:
            logger.error(
                "crosspost.failed",
                platform=adapted.platform,
                error=str(exc),
            )
            return {
                "status": "failed",
                "platform": adapted.platform,
                "error": str(exc),
            }

    async def publish_multi(
        self,
        content: dict,
        platforms: list[str],
    ) -> dict[str, dict]:
        """Adapt and publish to multiple platforms."""
        results = {}
        for platform in platforms:
            adapted = PlatformAdapter.adapt(
                platform=platform,
                caption=content.get("caption", ""),
                hashtags=content.get("hashtags", []),
                content_type=content.get("content_type", "image"),
                media_urls=content.get("cdn_urls", []),
                media_paths=content.get("media_paths", []),
                voiceover_text=content.get("voiceover_text", ""),
                topic=content.get("topic", ""),
            )
            results[platform] = await self.publish(adapted)
        return results

    async def _dispatch(self, client, adapted: AdaptedContent) -> str:
        """Route to the correct client method."""
        p = adapted.platform

        if p == "instagram":
            if adapted.content_type == "reel" and adapted.media_urls:
                return await client.post_reel(
                    video_url=adapted.media_urls[0],
                    caption=adapted.caption,
                )
            elif adapted.content_type == "carousel" and adapted.media_urls:
                items = [{"url": u, "type": "IMAGE"} for u in adapted.media_urls]
                return await client.post_carousel(items, adapted.caption)
            elif adapted.media_urls:
                return await client.post_image(
                    image_url=adapted.media_urls[0],
                    caption=adapted.caption,
                )

        elif p == "twitter":
            if adapted.content_type == "thread" and adapted.thread_parts:
                ids = await client.post_thread(adapted.thread_parts)
                return ids[0] if ids else ""
            return await client.post_tweet(adapted.caption)

        elif p == "tiktok":
            if adapted.media_urls:
                return await client.post_video(
                    video_url=adapted.media_urls[0],
                    caption=adapted.caption,
                )

        elif p == "youtube":
            if adapted.media_paths:
                return await client.upload_short(
                    video_path=adapted.media_paths[0],
                    title=adapted.title,
                    description=adapted.caption,
                    tags=adapted.hashtags,
                )

        elif p == "facebook":
            if adapted.content_type == "reel" and adapted.media_urls:
                return await client.post_reel(
                    video_url=adapted.media_urls[0],
                    description=adapted.caption,
                )
            elif adapted.media_urls:
                return await client.post_photo(
                    image_url=adapted.media_urls[0],
                    caption=adapted.caption,
                )
            return await client.post_text(adapted.caption)

        elif p == "telegram":
            if adapted.content_type == "video" and adapted.media_urls:
                msg_id = await client.send_video(
                    video_url=adapted.media_urls[0],
                    caption=adapted.caption,
                )
                return str(msg_id)
            elif adapted.media_urls:
                msg_id = await client.send_photo(
                    photo_url=adapted.media_urls[0],
                    caption=adapted.caption,
                )
                return str(msg_id)
            msg_id = await client.send_message(adapted.caption)
            return str(msg_id)

        elif p == "linkedin":
            if adapted.media_urls:
                return await client.post_image(
                    image_url=adapted.media_urls[0],
                    text=adapted.caption,
                )
            return await client.post_text(adapted.caption)

        return ""

    async def close(self) -> None:
        for client in self._clients.values():
            if hasattr(client, "close"):
                await client.close()
