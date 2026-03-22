"""Content recycler — repurpose top-performing content.

Strategies:
  1. Reel → Carousel (extract key frames + captions)
  2. Reel → Story (cut into 15s clips)
  3. Image → Story (add animation suggestions)
  4. Top post → New angle (same topic, different hook/style)
  5. Seasonal recycling (repost with updated context)
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from config import settings
from pipeline.orchestrator import ContentRequest

logger = structlog.get_logger(__name__)

HISTORY_FILE = Path(settings.content_output_dir) / "post_history.json"
PERFORMANCE_FILE = Path(settings.content_output_dir) / "performance.json"
RECYCLE_LOG = Path(settings.content_output_dir) / "recycle_log.json"


@dataclass
class RecycleCandidate:
    """A post that's worth repurposing."""

    original_id: str
    topic: str
    category: str
    content_type: str
    caption: str
    score: float  # Performance score
    posted_at: str
    strategy: str = ""  # How to recycle
    new_request: ContentRequest | None = None


# Recycling rules
RECYCLE_STRATEGIES = {
    "reel_to_carousel": {
        "source": "reel",
        "target": "carousel",
        "description": "Extract key moments into carousel slides",
        "min_days_since_post": 14,
    },
    "reel_to_story": {
        "source": "reel",
        "target": "story",
        "description": "Repurpose reel as story with poll/quiz sticker context",
        "min_days_since_post": 7,
    },
    "image_to_reel": {
        "source": "image",
        "target": "reel",
        "description": "Animate static image into reel with voiceover",
        "min_days_since_post": 21,
    },
    "new_angle": {
        "source": "*",
        "target": "*",
        "description": "Same topic, different visual style and hook",
        "min_days_since_post": 30,
    },
}

# Hook rotation for "new_angle" strategy
ALTERNATE_HOOKS = {
    "motivational": [
        "Bu oddiy qoidani bilsangiz, hayotingiz o'zgaradi",
        "Muvaffaqiyat formulasi: 3 ta muhim qadam",
        "Ko'pchilik bilmaydigan sir...",
    ],
    "educational": [
        "Bilasizmi? Bu haqiqat ko'pchilikni hayron qoldiradi",
        "5 ta fakt — oxirgisi sizni lol qoldiradi",
        "Mutaxassislar tavsiyasi:",
    ],
    "recipe": [
        "Bugungi taom — barmoqlaringizni yalaysiz!",
        "Eng oson retsept — 10 daqiqada tayyor",
        "Buvimning maxfiy retsepti:",
    ],
    "travel": [
        "O'zbekistonning eng go'zal joyi — ko'pchilik bilmaydi",
        "Bu joyni ko'rganlar lol qoladi",
        "Sayohat rejasi: 3 kun, 1 shahar, million taassurot",
    ],
}


class ContentRecycler:
    """Finds top-performing content and creates recycled variants."""

    def __init__(self) -> None:
        self._history = self._load_history()
        self._performance = self._load_performance()

    def find_candidates(
        self,
        strategy: str = "new_angle",
        limit: int = 5,
    ) -> list[RecycleCandidate]:
        """Find posts worth recycling based on performance."""
        rule = RECYCLE_STRATEGIES.get(strategy, RECYCLE_STRATEGIES["new_angle"])
        min_age = timedelta(days=rule["min_days_since_post"])
        now = datetime.now()

        candidates = []
        for post in self._history:
            if post.get("status") != "published":
                continue

            # Check source type match
            if rule["source"] != "*" and post.get("content_type") != rule["source"]:
                continue

            # Check age
            posted_at = post.get("timestamp", "")
            try:
                post_date = datetime.fromisoformat(posted_at)
                if now - post_date < min_age:
                    continue
            except (ValueError, TypeError):
                continue

            # Check if already recycled recently
            if self._was_recently_recycled(post.get("request_id", "")):
                continue

            # Score by performance
            perf = self._get_performance(post.get("media_id", ""))
            score = self._calculate_recycle_score(perf, post)

            candidates.append(RecycleCandidate(
                original_id=post.get("request_id", ""),
                topic=self._extract_topic(post),
                category=self._extract_category(post),
                content_type=post.get("content_type", "reel"),
                caption=post.get("caption", ""),
                score=score,
                posted_at=posted_at,
                strategy=strategy,
            ))

        # Sort by score (highest first)
        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:limit]

    def create_recycled_request(
        self,
        candidate: RecycleCandidate,
    ) -> ContentRequest:
        """Transform a recycle candidate into a new content request."""
        rule = RECYCLE_STRATEGIES.get(candidate.strategy, RECYCLE_STRATEGIES["new_angle"])
        target_type = rule["target"] if rule["target"] != "*" else candidate.content_type

        # Get alternate hook for the category
        hooks = ALTERNATE_HOOKS.get(candidate.category, ALTERNATE_HOOKS["motivational"])
        new_hook = random.choice(hooks)

        # Vary the style
        styles = ["photorealistic", "cinematic", "illustration"]
        new_style = random.choice([s for s in styles if s != "photorealistic"])

        request = ContentRequest(
            content_type=target_type,
            image_prompt=f"[RECYCLE:{candidate.strategy}] {candidate.topic}",
            caption=f"{new_hook}\n\n{candidate.caption[:500]}",
            image_style=new_style,
        )

        # Log the recycle
        self._log_recycle(candidate)

        logger.info(
            "recycler.created",
            original=candidate.original_id,
            strategy=candidate.strategy,
            new_type=target_type,
        )

        return request

    def get_recycle_report(self) -> str:
        """Display recycling opportunities."""
        lines = [
            "=" * 65,
            "  Content Recycling Report",
            "=" * 65,
        ]

        for strategy_name, rule in RECYCLE_STRATEGIES.items():
            candidates = self.find_candidates(strategy=strategy_name, limit=3)
            lines.append(f"\n  Strategy: {strategy_name}")
            lines.append(f"  {rule['description']}")
            lines.append(f"  Min age: {rule['min_days_since_post']} days")

            if candidates:
                for c in candidates:
                    lines.append(
                        f"    [{c.score:.1f}] {c.category}/{c.content_type} — "
                        f"{c.topic[:35]} ({c.posted_at[:10]})"
                    )
            else:
                lines.append("    No candidates found")

        lines.append(f"\n{'=' * 65}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _calculate_recycle_score(self, performance: dict, post: dict) -> float:
        """Score a post's recycling potential (0-10)."""
        score = 5.0  # Base score

        # Performance boost
        engagement = performance.get("engagement_rate", 0)
        score += min(3.0, engagement * 10)  # Up to +3 for engagement

        reach = performance.get("reach", 0)
        score += min(1.0, reach / 10000)  # Up to +1 for reach

        saves = performance.get("saves", 0)
        score += min(1.0, saves / 50)  # Up to +1 for saves (high intent signal)

        return min(10.0, score)

    def _extract_topic(self, post: dict) -> str:
        template_name = post.get("template", "")
        if ":" in template_name:
            return template_name.split(":", 1)[1]
        return template_name

    def _extract_category(self, post: dict) -> str:
        template_name = post.get("template", "")
        if ":" in template_name:
            return template_name.split(":")[0]
        return "motivational"

    def _get_performance(self, media_id: str) -> dict:
        for entry in self._performance:
            if entry.get("media_id") == media_id:
                return entry.get("metrics", {})
        return {}

    def _was_recently_recycled(self, original_id: str) -> bool:
        log = self._load_recycle_log()
        cutoff = (datetime.now() - timedelta(days=14)).isoformat()
        return any(
            entry.get("original_id") == original_id
            and entry.get("recycled_at", "") > cutoff
            for entry in log
        )

    def _log_recycle(self, candidate: RecycleCandidate) -> None:
        log = self._load_recycle_log()
        log.append({
            "original_id": candidate.original_id,
            "strategy": candidate.strategy,
            "category": candidate.category,
            "recycled_at": datetime.now().isoformat(),
        })
        RECYCLE_LOG.parent.mkdir(parents=True, exist_ok=True)
        RECYCLE_LOG.write_text(json.dumps(log, indent=2))

    def _load_history(self) -> list[dict]:
        if HISTORY_FILE.exists():
            try:
                return json.loads(HISTORY_FILE.read_text())
            except json.JSONDecodeError:
                return []
        return []

    def _load_performance(self) -> list[dict]:
        if PERFORMANCE_FILE.exists():
            try:
                return json.loads(PERFORMANCE_FILE.read_text())
            except json.JSONDecodeError:
                return []
        return []

    def _load_recycle_log(self) -> list[dict]:
        if RECYCLE_LOG.exists():
            try:
                return json.loads(RECYCLE_LOG.read_text())
            except json.JSONDecodeError:
                return []
        return []
