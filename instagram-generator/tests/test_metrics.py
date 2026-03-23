"""Tests for metrics collection system."""

import pytest

from utils.metrics import MetricsCollector


@pytest.fixture
def collector():
    c = MetricsCollector()
    c.reset()
    return c


class TestMetricsCollector:
    def test_counter_increment(self, collector):
        collector.inc("content_generated", content_type="reel")
        collector.inc("content_generated", content_type="reel")
        data = collector.get_all()
        assert data["counters"]['content_generated{content_type="reel"}'] == 2.0

    def test_gauge_set(self, collector):
        collector.set_gauge("queue_depth", 5.0)
        data = collector.get_all()
        assert data["gauges"]["queue_depth"] == 5.0

    def test_histogram_observe(self, collector):
        collector.observe("api_latency", 0.5, provider="nano_banana")
        collector.observe("api_latency", 1.2, provider="nano_banana")
        data = collector.get_all()
        key = 'api_latency{provider="nano_banana"}'
        assert data["histograms"][key]["count"] == 2
        assert data["histograms"][key]["avg"] == pytest.approx(0.85)

    def test_timer_context_manager(self, collector):
        with collector.timer("test_op"):
            pass  # Instant operation
        data = collector.get_all()
        assert "test_op" in data["histograms"]
        assert data["histograms"]["test_op"]["count"] == 1

    def test_prometheus_export(self, collector):
        collector.inc("requests_total", status="200")
        collector.set_gauge("active_workers", 3.0)
        output = collector.export_prometheus()
        assert "requests_total" in output
        assert "active_workers" in output
        assert "counter" in output
        assert "gauge" in output

    def test_display(self, collector):
        collector.inc("test_counter")
        output = collector.display()
        assert "Metrics" in output
        assert "test_counter" in output

    def test_reset(self, collector):
        collector.inc("should_be_cleared")
        collector.reset()
        data = collector.get_all()
        assert len(data["counters"]) == 0

    def test_histogram_retention(self, collector):
        for i in range(1100):
            collector.observe("big_metric", float(i))
        data = collector.get_all()
        assert data["histograms"]["big_metric"]["count"] <= 1000
