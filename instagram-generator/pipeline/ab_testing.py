"""A/B Testing — generate multiple content variants and track performance.

Flow:
  1. Agent crew generates N variants of the same topic
  2. Each variant differs in visual style, hook, or caption approach
  3. Variants are published at different times or to different audiences
  4. Performance is tracked and the winning strategy is promoted
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from agents.crew import CreativeCrew
from agents.base import CreativeBrief
from config import settings

logger = structlog.get_logger(__name__)

EXPERIMENTS_FILE = Path(settings.content_output_dir) / "ab_experiments.json"


@dataclass
class Variant:
    """A single content variant in an A/B test."""

    id: str = ""
    name: str = ""  # e.g., "variant_A", "variant_B"
    brief: dict = field(default_factory=dict)
    media_id: str = ""
    status: str = "pending"  # pending, published, tracked
    metrics: dict = field(default_factory=dict)  # reach, impressions, engagement, etc.

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:8]


@dataclass
class Experiment:
    """An A/B test experiment with multiple variants."""

    id: str = ""
    topic: str = ""
    category: str = ""
    content_type: str = "reel"
    variants: list[Variant] = field(default_factory=list)
    winner: str = ""  # variant id
    status: str = "created"  # created, running, completed
    created_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:10]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


# Variation strategies — what to change between variants
VARIATION_STRATEGIES = {
    "visual_style": {
        "description": "Same content, different visual styles",
        "variations": [
            {"style_preset": "photorealistic", "name": "Photorealistic"},
            {"style_preset": "cinematic", "name": "Cinematic"},
            {"style_preset": "illustration", "name": "Illustration"},
        ],
    },
    "hook_style": {
        "description": "Same visuals, different hook approaches",
        "variations": [
            {"hook_approach": "question", "name": "Question Hook"},
            {"hook_approach": "statement", "name": "Statement Hook"},
            {"hook_approach": "number", "name": "Number Hook"},
        ],
    },
    "pacing": {
        "description": "Same content, different video pacing",
        "variations": [
            {"pacing": "cinematic_slow", "name": "Cinematic Slow"},
            {"pacing": "dynamic_fast", "name": "Dynamic Fast"},
        ],
    },
    "duration": {
        "description": "Same content, different video lengths",
        "variations": [
            {"duration": "5", "name": "5 Second"},
            {"duration": "10", "name": "10 Second"},
        ],
    },
}


class ABTestingEngine:
    """Creates and manages A/B test experiments."""

    def __init__(self) -> None:
        self.crew = CreativeCrew()
        self._experiments: list[Experiment] = []
        self._load()

    async def create_experiment(
        self,
        topic: str,
        category: str,
        content_type: str = "reel",
        strategy: str = "visual_style",
        variant_count: int | None = None,
    ) -> Experiment:
        """Create a new A/B test with multiple content variants."""
        strat = VARIATION_STRATEGIES.get(strategy, VARIATION_STRATEGIES["visual_style"])
        count = variant_count or settings.ab_variant_count
        variations = strat["variations"][:count]

        experiment = Experiment(
            topic=topic,
            category=category,
            content_type=content_type,
        )

        logger.info(
            "ab.create_experiment",
            id=experiment.id,
            strategy=strategy,
            variants=len(variations),
        )

        for var_config in variations:
            # Generate a creative brief with this variation's parameters
            style = var_config.get("style_preset", "photorealistic")
            duration = var_config.get("duration", "5")

            brief = await self.crew.produce(
                topic=topic,
                category=category,
                content_type=content_type,
                style_preset=style,
                duration=duration,
            )

            variant = Variant(
                name=var_config.get("name", f"Variant {len(experiment.variants) + 1}"),
                brief=self.crew.brief_to_content_request(brief),
            )
            experiment.variants.append(variant)

        experiment.status = "running"
        self._experiments.append(experiment)
        self._save()

        return experiment

    def record_metrics(
        self,
        experiment_id: str,
        variant_id: str,
        metrics: dict,
    ) -> None:
        """Record performance metrics for a variant."""
        exp = self._find_experiment(experiment_id)
        if not exp:
            return

        for variant in exp.variants:
            if variant.id == variant_id:
                variant.metrics.update(metrics)
                variant.status = "tracked"
                break

        # Check if all variants have metrics — determine winner
        all_tracked = all(v.status == "tracked" for v in exp.variants)
        if all_tracked:
            exp.winner = self._determine_winner(exp)
            exp.status = "completed"
            logger.info(
                "ab.experiment_completed",
                id=experiment_id,
                winner=exp.winner,
            )

        self._save()

    def get_winner(self, experiment_id: str) -> Variant | None:
        """Get the winning variant of a completed experiment."""
        exp = self._find_experiment(experiment_id)
        if not exp or not exp.winner:
            return None
        for v in exp.variants:
            if v.id == exp.winner:
                return v
        return None

    def display_results(self, experiment_id: str) -> str:
        """Display experiment results."""
        exp = self._find_experiment(experiment_id)
        if not exp:
            return f"Experiment {experiment_id} not found."

        lines = [
            f"{'='*60}",
            f"  A/B Test: {exp.id}",
            f"  Topic: {exp.topic} | Category: {exp.category}",
            f"  Status: {exp.status}",
            f"{'='*60}",
        ]

        for v in exp.variants:
            winner_mark = " << WINNER" if v.id == exp.winner else ""
            lines.append(f"\n  {v.name} ({v.id}){winner_mark}")
            lines.append(f"    Status: {v.status}")
            if v.metrics:
                for k, val in v.metrics.items():
                    lines.append(f"    {k}: {val}")

        lines.append(f"\n{'='*60}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _determine_winner(self, exp: Experiment) -> str:
        """Pick the best variant based on engagement metrics."""
        best_score = -1
        best_id = ""

        for variant in exp.variants:
            m = variant.metrics
            # Composite score: engagement_rate * 0.4 + reach * 0.3 + saves * 0.3
            score = (
                m.get("engagement_rate", 0) * 0.4
                + m.get("reach", 0) / 1000 * 0.3
                + m.get("saves", 0) * 0.3
            )
            if score > best_score:
                best_score = score
                best_id = variant.id

        return best_id

    def _find_experiment(self, exp_id: str) -> Experiment | None:
        for exp in self._experiments:
            if exp.id == exp_id:
                return exp
        return None

    def _load(self) -> None:
        if EXPERIMENTS_FILE.exists():
            try:
                data = json.loads(EXPERIMENTS_FILE.read_text())
                self._experiments = []
                for d in data:
                    variants = [Variant(**v) for v in d.pop("variants", [])]
                    exp = Experiment(**d, variants=variants)
                    self._experiments.append(exp)
            except (json.JSONDecodeError, TypeError):
                self._experiments = []

    def _save(self) -> None:
        EXPERIMENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = []
        for exp in self._experiments:
            d = {
                "id": exp.id,
                "topic": exp.topic,
                "category": exp.category,
                "content_type": exp.content_type,
                "variants": [asdict(v) for v in exp.variants],
                "winner": exp.winner,
                "status": exp.status,
                "created_at": exp.created_at,
            }
            data.append(d)
        EXPERIMENTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
