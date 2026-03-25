"""Tests for the multi-agent creative system."""

from __future__ import annotations

import pytest

from agents.base import CreativeBrief, CreativeAgent, AgentRole


class TestCreativeBrief:
    def test_default_values(self):
        brief = CreativeBrief()
        assert brief.content_type == "reel"
        assert brief.language == "uz"
        assert brief.approved is False
        assert brief.quality_scores == {}

    def test_custom_values(self, sample_brief):
        assert sample_brief.topic == "Muvaffaqiyat sirlari"
        assert sample_brief.category == "motivational"
        assert sample_brief.approved is True
        assert len(sample_brief.quality_scores) == 4

    def test_quality_scores(self, sample_brief):
        assert sample_brief.quality_scores["visual_quality"] == 8.5
        assert sample_brief.quality_scores["cultural_sensitivity"] == 9.0


class TestCreativeAgent:
    def test_base_agent_has_default_role(self):
        agent = CreativeAgent()
        assert agent.role == AgentRole.DIRECTOR

    @pytest.mark.asyncio
    async def test_agent_processes_brief(self, sample_brief):
        from agents.director import DirectorAgent

        agent = DirectorAgent()
        result = await agent.process(sample_brief)
        assert isinstance(result, CreativeBrief)
        # Director should preserve topic and category
        assert result.topic == sample_brief.topic
        assert result.category == sample_brief.category
