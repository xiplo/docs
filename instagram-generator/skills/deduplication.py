"""Content duplication detection — prevent posting similar content.

Detection methods:
  - Exact match: identical topic + category
  - Fuzzy title: similar titles (token overlap ratio)
  - Caption similarity: overlapping n-grams
  - Recent window: only check against posts from last N days
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)


class DuplicateDetector:
    """Detect similar/duplicate content before publishing."""

    SIMILARITY_THRESHOLD = 0.65  # 65% overlap = duplicate
    LOOKBACK_DAYS = 30

    @classmethod
    def is_duplicate(
        cls,
        topic: str,
        caption: str = "",
        category: str = "",
        threshold: float | None = None,
    ) -> tuple[bool, str]:
        """Check if content is a duplicate.

        Returns (is_dup, reason).
        """
        thresh = threshold or cls.SIMILARITY_THRESHOLD
        history = cls._load_recent()

        for entry in history:
            # Exact topic match
            if entry.get("topic", "").lower() == topic.lower() and entry.get("category", "") == category:
                return True, f"Exact topic match: '{topic}' (posted {entry.get('timestamp', '')[:10]})"

            # Fuzzy title similarity
            if topic:
                sim = cls._token_similarity(topic, entry.get("topic", ""))
                if sim >= thresh:
                    return True, f"Similar topic ({sim:.0%}): '{entry.get('topic', '')[:40]}'"

            # Caption similarity
            if caption and entry.get("caption", ""):
                sim = cls._ngram_similarity(caption, entry.get("caption", ""))
                if sim >= thresh:
                    return True, f"Similar caption ({sim:.0%})"

        return False, ""

    @classmethod
    def find_similar(
        cls,
        topic: str,
        limit: int = 5,
    ) -> list[dict]:
        """Find similar content from history."""
        history = cls._load_recent()
        scored = []

        for entry in history:
            sim = cls._token_similarity(topic, entry.get("topic", ""))
            if sim > 0.3:
                scored.append({
                    "topic": entry.get("topic", ""),
                    "category": entry.get("category", ""),
                    "similarity": round(sim, 2),
                    "posted": entry.get("timestamp", "")[:10],
                })

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    @classmethod
    def _token_similarity(cls, a: str, b: str) -> float:
        """Token overlap ratio between two strings."""
        tokens_a = set(cls._tokenize(a))
        tokens_b = set(cls._tokenize(b))
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        return len(intersection) / len(union) if union else 0.0

    @classmethod
    def _ngram_similarity(cls, a: str, b: str, n: int = 3) -> float:
        """Character n-gram overlap ratio."""
        ngrams_a = Counter(cls._ngrams(a, n))
        ngrams_b = Counter(cls._ngrams(b, n))
        if not ngrams_a or not ngrams_b:
            return 0.0
        intersection = sum((ngrams_a & ngrams_b).values())
        union = sum((ngrams_a | ngrams_b).values())
        return intersection / union if union else 0.0

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        """Simple word tokenization."""
        text = text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        return [w for w in text.split() if len(w) > 2]

    @classmethod
    def _ngrams(cls, text: str, n: int) -> list[str]:
        text = text.lower().strip()
        return [text[i:i + n] for i in range(len(text) - n + 1)]

    @classmethod
    def _load_recent(cls) -> list[dict]:
        """Load recent post history within lookback window."""
        history_file = Path(settings.content_output_dir) / "post_history.json"
        if not history_file.exists():
            return []

        try:
            all_posts = json.loads(history_file.read_text())
        except json.JSONDecodeError:
            return []

        cutoff = (datetime.now() - timedelta(days=cls.LOOKBACK_DAYS)).isoformat()
        return [p for p in all_posts if p.get("timestamp", "") >= cutoff]

    @classmethod
    def display(cls, topic: str = "") -> str:
        lines = [
            "=" * 60,
            "  Duplicate Detection",
            "=" * 60,
            f"  Threshold: {cls.SIMILARITY_THRESHOLD:.0%}",
            f"  Lookback: {cls.LOOKBACK_DAYS} days",
        ]

        if topic:
            is_dup, reason = cls.is_duplicate(topic)
            lines.append(f"\n  Topic: '{topic}'")
            if is_dup:
                lines.append(f"  DUPLICATE: {reason}")
            else:
                lines.append("  No duplicates found.")

            similar = cls.find_similar(topic)
            if similar:
                lines.append(f"\n  Similar content:")
                for s in similar:
                    lines.append(
                        f"    {s['similarity']:.0%}  {s['topic'][:40]}  ({s['posted']})"
                    )

        lines.append("=" * 60)
        return "\n".join(lines)
