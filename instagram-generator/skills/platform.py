"""Platform skills — Instagram-specific optimization rules."""

from __future__ import annotations


class PlatformSkills:
    """Instagram platform rules and optimization strategies."""

    # Instagram algorithm signals (2024-2025)
    ALGORITHM_SIGNALS = {
        "reels": {
            "positive": [
                "watch_time > 80%",
                "replays",
                "shares_to_stories",
                "saves",
                "comments",
                "follows_from_reel",
            ],
            "negative": [
                "skip_in_first_3s",
                "watermarks_from_other_platforms",
                "low_resolution",
                "blurry_content",
            ],
            "tips": [
                "Hook in first 1.5 seconds",
                "Use trending audio",
                "Text overlay for sound-off viewers",
                "Vertical 9:16 full screen",
                "3-15 second sweet spot",
                "Loop-friendly ending",
            ],
        },
        "carousel": {
            "positive": [
                "all_slides_viewed",
                "saves",
                "shares",
                "time_spent",
                "return_visits",
            ],
            "tips": [
                "First slide is scroll-stopper",
                "Consistent visual style across slides",
                "Teach something in each slide",
                "Last slide has clear CTA",
                "3-7 slides optimal",
            ],
        },
        "stories": {
            "positive": [
                "replies",
                "sticker_interactions",
                "holds_on_story",
                "shares",
            ],
            "tips": [
                "Use interactive stickers (polls, questions)",
                "Keep text in safe zones",
                "Swipe-up CTA (if 10k+ followers)",
                "Behind-the-scenes content performs well",
            ],
        },
    }

    # Optimal posting specs
    SPECS = {
        "reel": {
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "max_duration_s": 90,
            "sweet_spot_s": (7, 15),
            "max_file_mb": 250,
            "format": "mp4",
            "codec": "H.264",
            "audio": "AAC, 44.1kHz",
        },
        "feed_image": {
            "aspect_ratio": "4:5",
            "resolution": "1080x1350",
            "max_file_mb": 8,
            "format": "jpg/png",
            "dpi": 72,
        },
        "carousel": {
            "aspect_ratio": "1:1 or 4:5",
            "resolution": "1080x1080 or 1080x1350",
            "max_slides": 10,
            "format": "jpg/png/mp4",
        },
        "story": {
            "aspect_ratio": "9:16",
            "resolution": "1080x1920",
            "max_duration_s": 60,
            "format": "jpg/png/mp4",
        },
    }

    @classmethod
    def get_specs(cls, content_type: str) -> dict:
        return cls.SPECS.get(content_type, cls.SPECS["reel"])

    @classmethod
    def get_algorithm_tips(cls, content_type: str) -> list[str]:
        key = "reels" if content_type == "reel" else content_type
        signals = cls.ALGORITHM_SIGNALS.get(key, {})
        return signals.get("tips", [])

    @classmethod
    def validate_caption_length(cls, caption: str) -> dict[str, any]:
        """Validate and analyze caption length."""
        length = len(caption)
        preview_cutoff = 125  # Characters shown before "...more"
        max_length = 2200

        return {
            "length": length,
            "within_limit": length <= max_length,
            "preview_text": caption[:preview_cutoff],
            "full_visible_without_expand": length <= preview_cutoff,
            "recommendation": (
                "Good — full caption visible"
                if length <= preview_cutoff
                else f"Caption truncated at {preview_cutoff} chars. "
                f"Put hook in first {preview_cutoff} characters."
            ),
        }

    @classmethod
    def optimize_hashtag_strategy(
        cls, hashtags: list[str], follower_count: int = 1000
    ) -> dict[str, list[str]]:
        """Organize hashtags by reach tier."""
        # Strategy: mix of small/medium/large hashtags
        if follower_count < 5000:
            return {
                "strategy": "small_account_growth",
                "mix": "60% small niche, 30% medium, 10% large",
                "recommended_count": 20,
                "hashtags": hashtags[:20],
            }
        elif follower_count < 50000:
            return {
                "strategy": "mid_account_expansion",
                "mix": "40% small niche, 40% medium, 20% large",
                "recommended_count": 15,
                "hashtags": hashtags[:15],
            }
        else:
            return {
                "strategy": "large_account_authority",
                "mix": "20% niche, 30% medium, 50% branded/large",
                "recommended_count": 10,
                "hashtags": hashtags[:10],
            }

    @staticmethod
    def get_safe_zones() -> dict[str, dict]:
        """Get safe zones for text placement (avoiding IG UI elements)."""
        return {
            "reel": {
                "top_safe": {"y_start": 0.12, "y_end": 0.15},
                "content_area": {"y_start": 0.15, "y_end": 0.75},
                "bottom_avoid": {"y_start": 0.75, "note": "IG UI: like/comment/share buttons"},
                "right_avoid": {"x_start": 0.85, "note": "IG UI: action buttons column"},
            },
            "story": {
                "top_avoid": {"y_end": 0.10, "note": "Profile pic / close button"},
                "content_area": {"y_start": 0.10, "y_end": 0.85},
                "bottom_avoid": {"y_start": 0.85, "note": "Reply bar / send message"},
            },
        }
