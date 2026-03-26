"""Engagement optimizer — find best posting times per platform.

Analyzes historical performance to recommend:
  - Best time of day per platform
  - Best day of week per category
  - Optimal posting frequency
  - Platform-specific engagement patterns
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

HISTORY_FILE = Path(settings.content_output_dir) / "post_history.json"

# Optimal posting times per platform — Tashkent timezone (2026 research-backed)
# Uzbekistan peak: morning commute, lunch break, evening scroll
DEFAULT_BEST_TIMES: dict[str, list[str]] = {
    "instagram": ["09:00", "12:30", "18:00", "21:00"],
    "twitter": ["08:00", "12:00", "17:00", "21:00"],
    "tiktok": ["07:00", "10:00", "19:00", "22:00"],
    "youtube": ["12:00", "15:00", "18:00"],
    "facebook": ["09:00", "13:00", "16:00"],
    "telegram": ["08:00", "12:00", "18:00", "21:00"],
    "linkedin": ["07:30", "10:00", "12:00"],
    "pinterest": ["12:00", "18:00", "21:00"],
    "threads": ["09:00", "12:00", "18:00"],
}

# Best days per platform (2026 data)
DEFAULT_BEST_DAYS: dict[str, list[str]] = {
    "instagram": ["Tuesday", "Wednesday", "Thursday"],
    "twitter": ["Monday", "Tuesday", "Wednesday"],
    "tiktok": ["Tuesday", "Thursday", "Saturday"],
    "youtube": ["Friday", "Saturday"],
    "facebook": ["Wednesday", "Thursday", "Friday"],
    "telegram": ["Monday", "Wednesday", "Friday"],
    "linkedin": ["Tuesday", "Wednesday", "Thursday"],
    "pinterest": ["Saturday", "Sunday", "Friday"],
    "threads": ["Tuesday", "Wednesday", "Thursday"],
}


@dataclass
class TimeSlotScore:
    """Performance score for a time slot."""

    time: str
    platform: str = ""
    posts: int = 0
    avg_engagement: float = 0.0
    avg_reach: int = 0
    score: float = 0.0


@dataclass
class OptimizationResult:
    """Recommendation from the optimizer."""

    platform: str
    best_times: list[str] = field(default_factory=list)
    best_days: list[str] = field(default_factory=list)
    recommended_frequency: int = 3  # posts per day
    confidence: str = "default"  # default, low, medium, high
    notes: list[str] = field(default_factory=list)


class EngagementOptimizer:
    """Analyze posting history and optimize timing."""

    MIN_POSTS_FOR_ANALYSIS = 10

    @classmethod
    def optimize(cls, platform: str = "") -> list[OptimizationResult]:
        """Get posting recommendations for one or all platforms."""
        history = cls._load_history()
        platforms = [platform] if platform else list(DEFAULT_BEST_TIMES.keys())
        results = []

        for p in platforms:
            result = cls._analyze_platform(p, history)
            results.append(result)

        return results

    @classmethod
    def get_best_time(cls, platform: str) -> str:
        """Get the single best posting time for a platform."""
        result = cls._analyze_platform(platform, cls._load_history())
        return result.best_times[0] if result.best_times else "12:00"

    @classmethod
    def get_schedule(cls, platforms: list[str], posts_per_day: int = 3) -> dict[str, list[str]]:
        """Generate an optimized posting schedule across platforms."""
        schedule: dict[str, list[str]] = {}

        for platform in platforms:
            result = cls._analyze_platform(platform, cls._load_history())
            schedule[platform] = result.best_times[:posts_per_day]

        return schedule

    @classmethod
    def _analyze_platform(cls, platform: str, history: list[dict]) -> OptimizationResult:
        """Analyze posting history for a single platform."""
        # Filter history for this platform (if tagged)
        platform_posts = [
            h for h in history
            if h.get("platform", "instagram") == platform
            or (platform == "instagram" and "platform" not in h)
        ]

        if len(platform_posts) < cls.MIN_POSTS_FOR_ANALYSIS:
            # Not enough data — use defaults
            return OptimizationResult(
                platform=platform,
                best_times=DEFAULT_BEST_TIMES.get(platform, ["12:00"]),
                best_days=DEFAULT_BEST_DAYS.get(platform, ["Wednesday"]),
                confidence="default",
                notes=[f"Using defaults (only {len(platform_posts)} posts, need {cls.MIN_POSTS_FOR_ANALYSIS})"],
            )

        # Analyze by time slot
        time_scores: dict[str, list[float]] = defaultdict(list)
        day_scores: dict[str, list[float]] = defaultdict(list)

        for post in platform_posts:
            ts = post.get("timestamp", "")
            if not ts:
                continue

            try:
                dt = datetime.fromisoformat(ts)
                hour = dt.strftime("%H:00")
                day = dt.strftime("%A")

                # Score based on status
                score = 1.0 if post.get("status") == "published" else 0.0
                time_scores[hour].append(score)
                day_scores[day].append(score)
            except (ValueError, TypeError):
                continue

        # Rank time slots
        best_times = sorted(
            time_scores.keys(),
            key=lambda t: sum(time_scores[t]) / len(time_scores[t]) if time_scores[t] else 0,
            reverse=True,
        )[:4]

        # Rank days
        best_days = sorted(
            day_scores.keys(),
            key=lambda d: sum(day_scores[d]) / len(day_scores[d]) if day_scores[d] else 0,
            reverse=True,
        )[:3]

        confidence = "high" if len(platform_posts) >= 50 else "medium"

        return OptimizationResult(
            platform=platform,
            best_times=best_times or DEFAULT_BEST_TIMES.get(platform, ["12:00"]),
            best_days=best_days or DEFAULT_BEST_DAYS.get(platform, ["Wednesday"]),
            confidence=confidence,
            notes=[f"Analyzed {len(platform_posts)} posts"],
        )

    @classmethod
    def display(cls) -> str:
        results = cls.optimize()
        lines = [
            "=" * 65,
            "  Engagement Optimizer — Best Posting Times",
            "=" * 65,
        ]

        for r in results:
            times = ", ".join(r.best_times[:3])
            days = ", ".join(r.best_days[:3])
            lines.append(f"\n  {r.platform.upper()} (confidence: {r.confidence})")
            lines.append(f"    Best times: {times}")
            lines.append(f"    Best days:  {days}")
            lines.append(f"    Frequency:  {r.recommended_frequency}/day")
            for note in r.notes:
                lines.append(f"    Note: {note}")

        lines.append("=" * 65)
        return "\n".join(lines)

    @classmethod
    def _load_history(cls) -> list[dict]:
        if HISTORY_FILE.exists():
            try:
                return json.loads(HISTORY_FILE.read_text())
            except json.JSONDecodeError:
                return []
        return []
