"""Tests for plugin system."""

import pytest

from plugins import PluginRegistry


@pytest.fixture
def registry():
    r = PluginRegistry()
    r.reset()
    return r


class TestPluginRegistry:
    def test_register_plugin(self, registry):
        registry.register_plugin("test_plugin", {"version": "1.0"})
        plugins = registry.get_plugins()
        assert "test_plugin" in plugins
        assert plugins["test_plugin"]["version"] == "1.0"

    def test_register_hook(self, registry):
        called = []
        registry.register_hook("on_published", lambda **kw: called.append(kw))

        counts = registry.get_hooks_count()
        assert counts["on_published"] == 1

    @pytest.mark.asyncio
    async def test_emit_sync_hook(self, registry):
        results = []
        registry.register_hook("on_published", lambda **kw: results.append(kw.get("media_id")))

        await registry.emit("on_published", media_id="123")
        assert results == ["123"]

    @pytest.mark.asyncio
    async def test_emit_async_hook(self, registry):
        results = []

        async def async_handler(**kw):
            results.append(kw.get("topic"))

        registry.register_hook("on_pre_generate", async_handler)
        await registry.emit("on_pre_generate", topic="test")
        assert results == ["test"]

    @pytest.mark.asyncio
    async def test_emit_handles_errors(self, registry):
        def bad_hook(**kw):
            raise ValueError("boom")

        registry.register_hook("on_failed", bad_hook)
        # Should not raise
        results = await registry.emit("on_failed", error="test")
        assert results == []

    def test_unknown_event(self, registry):
        # Should not raise
        registry.register_hook("on_nonexistent", lambda **kw: None)

    def test_display(self, registry):
        registry.register_plugin("display_test", {"version": "2.0", "description": "Test"})
        output = registry.display()
        assert "Plugin System" in output
        assert "display_test" in output

    def test_reset(self, registry):
        registry.register_plugin("temp", {"version": "0"})
        registry.reset()
        assert len(registry.get_plugins()) == 0


class TestExampleLoggerPlugin:
    def test_load_example_plugin(self, registry):
        from plugins.example_logger import register
        register(registry)

        plugins = registry.get_plugins()
        assert "example_logger" in plugins
        assert registry.get_hooks_count()["on_pre_generate"] == 1
        assert registry.get_hooks_count()["on_published"] == 1
        assert registry.get_hooks_count()["on_failed"] == 1
