"""Metrics collection — lightweight Prometheus-compatible metrics.

Collects:
  - Content generation counts (by type, status)
  - API call latencies (by provider)
  - Queue depth over time
  - Error rates

Exports:
  - /metrics endpoint (Prometheus text format)
  - JSON dump for dashboard
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import Lock

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MetricPoint:
    """A single metric observation."""

    name: str
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = time.time()


class MetricsCollector:
    """Thread-safe metrics collection."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._lock = Lock()
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = defaultdict(list)
        self._labels: dict[str, dict[str, str]] = {}

    def inc(self, name: str, value: float = 1.0, **labels) -> None:
        """Increment a counter."""
        key = self._key(name, labels)
        with self._lock:
            self._counters[key] += value
            if labels:
                self._labels[key] = labels

    def set_gauge(self, name: str, value: float, **labels) -> None:
        """Set a gauge value."""
        key = self._key(name, labels)
        with self._lock:
            self._gauges[key] = value
            if labels:
                self._labels[key] = labels

    def observe(self, name: str, value: float, **labels) -> None:
        """Record a histogram observation."""
        key = self._key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            if labels:
                self._labels[key] = labels
            # Keep last 1000 observations
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-500:]

    @contextmanager
    def timer(self, name: str, **labels):
        """Context manager to time operations."""
        start = time.monotonic()
        try:
            yield
        finally:
            duration = time.monotonic() - start
            self.observe(name, duration, **labels)

    def get_all(self) -> dict:
        """Get all metrics as a dict."""
        with self._lock:
            result = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
            }
            for key, values in self._histograms.items():
                if values:
                    result["histograms"][key] = {
                        "count": len(values),
                        "sum": sum(values),
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "p50": sorted(values)[len(values) // 2],
                        "p95": sorted(values)[int(len(values) * 0.95)],
                    }
            return result

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        lines = []

        with self._lock:
            for key, value in sorted(self._counters.items()):
                labels = self._labels.get(key, {})
                label_str = self._format_labels(labels)
                base_name = key.split("{")[0] if "{" in key else key
                lines.append(f"# TYPE {base_name} counter")
                lines.append(f"{key}{label_str} {value}")

            for key, value in sorted(self._gauges.items()):
                labels = self._labels.get(key, {})
                label_str = self._format_labels(labels)
                base_name = key.split("{")[0] if "{" in key else key
                lines.append(f"# TYPE {base_name} gauge")
                lines.append(f"{key}{label_str} {value}")

            for key, values in sorted(self._histograms.items()):
                if values:
                    labels = self._labels.get(key, {})
                    label_str = self._format_labels(labels)
                    lines.append(f"# TYPE {key} summary")
                    lines.append(f"{key}_count{label_str} {len(values)}")
                    lines.append(f"{key}_sum{label_str} {sum(values):.4f}")

        return "\n".join(lines) + "\n"

    def display(self) -> str:
        """Human-readable metrics display."""
        data = self.get_all()
        lines = [
            "=" * 60,
            "  System Metrics",
            "=" * 60,
        ]

        if data["counters"]:
            lines.append("\n  Counters:")
            for key, val in sorted(data["counters"].items()):
                lines.append(f"    {key:<40} {val:.0f}")

        if data["gauges"]:
            lines.append("\n  Gauges:")
            for key, val in sorted(data["gauges"].items()):
                lines.append(f"    {key:<40} {val:.2f}")

        if data["histograms"]:
            lines.append("\n  Histograms:")
            for key, stats in sorted(data["histograms"].items()):
                lines.append(f"    {key}:")
                lines.append(
                    f"      count={stats['count']}  avg={stats['avg']:.3f}s  "
                    f"p50={stats['p50']:.3f}s  p95={stats['p95']:.3f}s"
                )

        lines.append("=" * 60)
        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics (for testing)."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._labels.clear()

    @staticmethod
    def _key(name: str, labels: dict) -> str:
        if not labels:
            return name
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{parts}}}"

    @staticmethod
    def _format_labels(labels: dict) -> str:
        if not labels:
            return ""
        parts = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{{{parts}}}"


# Singleton instance
metrics = MetricsCollector()
