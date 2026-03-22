"""Analytics skills — data-driven content optimization."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

HISTORY_FILE = Path(settings.content_output_dir) / "post_history.json"
PERFORMANCE_FILE = Path(settings.content_output_dir) / "performance.json"


class AnalyticsSkills:
    """Skills for analyzing content performance and optimizing strategy."""

    @staticmethod
    def load_history() -> list[dict]:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text())
        return []

    @classmethod
    def get_best_performing_category(cls) -> str | None:
        """Find which category gets the best results historically."""
        history = cls.load_history()
        if not history:
            return None

        # Count successes by category (using template name as proxy)
        category_map = {
            "morning_motivation": "motivational",
            "success_mindset": "motivational",
            "tech_tips": "educational",
            "product_launch": "product",
            "uzbekistan_travel": "travel",
            "uzbek_plov": "recipe",
            "fashion_lookbook": "fashion",
            "daily_quote_story": "motivational",
        }

        scores: dict[str, int] = {}
        for record in history:
            cat = category_map.get(record.get("template", ""), "unknown")
            if record.get("status") == "published":
                scores[cat] = scores.get(cat, 0) + 1

        if scores:
            return max(scores, key=scores.get)
        return None

    @classmethod
    def get_best_posting_time(cls) -> str | None:
        """Analyze history to find the best posting time."""
        history = cls.load_history()
        if not history:
            return None

        time_scores: dict[str, int] = {}
        for record in history:
            slot = record.get("time_slot", "")
            if record.get("status") == "published":
                time_scores[slot] = time_scores.get(slot, 0) + 1

        if time_scores:
            return max(time_scores, key=time_scores.get)
        return None

    @classmethod
    def get_success_rate(cls) -> float:
        """Calculate overall content generation success rate."""
        history = cls.load_history()
        if not history:
            return 0.0

        published = sum(1 for r in history if r.get("status") == "published")
        return published / len(history)

    @classmethod
    def get_category_distribution(cls) -> dict[str, int]:
        """Show how content is distributed across categories."""
        history = cls.load_history()
        dist: dict[str, int] = {}
        for record in history:
            ct = record.get("content_type", "unknown")
            dist[ct] = dist.get(ct, 0) + 1
        return dist

    @classmethod
    def suggest_next_content(cls) -> dict[str, str]:
        """Suggest what to post next based on analytics."""
        best_cat = cls.get_best_performing_category()
        dist = cls.get_category_distribution()

        # Find underrepresented content types
        all_types = {"reel", "image", "carousel", "story"}
        posted_types = set(dist.keys())
        missing = all_types - posted_types

        suggestion = {
            "recommended_category": best_cat or "motivational",
            "recommended_type": missing.pop() if missing else "reel",
            "reasoning": "",
        }

        if missing:
            suggestion["reasoning"] = (
                f"Content type '{suggestion['recommended_type']}' hasn't been used yet. "
                "Diversifying content types improves reach."
            )
        elif best_cat:
            suggestion["reasoning"] = (
                f"Category '{best_cat}' performs best historically. "
                "Continue with what works while testing new formats."
            )
        else:
            suggestion["reasoning"] = "No history yet. Starting with motivational reels."

        return suggestion

    @classmethod
    def generate_report(cls) -> str:
        """Generate a text report of content performance."""
        history = cls.load_history()
        if not history:
            return "No posting history available."

        total = len(history)
        published = sum(1 for r in history if r.get("status") == "published")
        failed = total - published
        rate = (published / total * 100) if total else 0

        dist = cls.get_category_distribution()
        best_cat = cls.get_best_performing_category()
        best_time = cls.get_best_posting_time()

        lines = [
            "=" * 50,
            "  Instagram Content Generator — Analytics Report",
            "=" * 50,
            f"  Total posts attempted: {total}",
            f"  Successfully published: {published}",
            f"  Failed: {failed}",
            f"  Success rate: {rate:.1f}%",
            "",
            "  Content type distribution:",
        ]
        for ct, count in sorted(dist.items()):
            lines.append(f"    {ct}: {count}")

        if best_cat:
            lines.append(f"\n  Best performing category: {best_cat}")
        if best_time:
            lines.append(f"  Best posting time: {best_time}")

        lines.append("=" * 50)
        return "\n".join(lines)
