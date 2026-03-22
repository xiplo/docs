#!/usr/bin/env python3
"""CLI entry point for the Instagram Content Generator.

Usage:
    # AI-driven generation with agent system
    python main.py auto-generate --category motivational --topic "Muvaffaqiyat"

    # Generate from template (direct)
    python main.py generate --template morning_motivation

    # Plan weekly content calendar
    python main.py strategy --plan-week

    # Start the automated scheduler
    python main.py schedule

    # View analytics report
    python main.py analytics

    # List available templates
    python main.py templates
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
import structlog

from config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(colors=True),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Instagram Content Generator — Multi-Agent Creative System

    Nano Banana (images) + Kling 3.0 (video) + Eleven Labs (Uzbek TTS)
    """
    pass


# =====================================================================
# auto-generate command (agent-driven)
# =====================================================================


@cli.command("auto-generate")
@click.option("--category", "-c", required=True,
              type=click.Choice([
                  "motivational", "educational", "product", "travel",
                  "recipe", "fashion", "tech", "lifestyle", "humor",
              ]))
@click.option("--topic", "-t", default=None, help="Content topic (auto-selected if omitted)")
@click.option("--content-type", "-ct", default="reel",
              type=click.Choice(["reel", "image", "carousel", "story"]))
@click.option("--style", "-s", default="photorealistic",
              type=click.Choice([
                  "photorealistic", "cinematic", "illustration",
                  "3d_render", "flat_design", "anime", "watercolor",
              ]))
@click.option("--duration", "-d", default="5", type=click.Choice(["5", "10"]))
@click.option("--dry-run", is_flag=True, help="Preview without posting")
def auto_generate(
    category: str,
    topic: str | None,
    content_type: str,
    style: str,
    duration: str,
    dry_run: bool,
):
    """Generate content using the multi-agent creative system."""
    from agents.crew import CreativeCrew
    from pipeline.orchestrator import ContentPipeline, ContentRequest
    from strategy.engine import StrategyEngine

    if not topic:
        engine = StrategyEngine()
        topic = engine.suggest_topic(category)
        click.echo(f"  Auto-selected topic: {topic}")

    async def _run():
        # Phase 1: Agent crew produces a creative brief
        click.echo(f"\n{'='*60}")
        click.echo(f"  CREATIVE CREW — Agent Pipeline")
        click.echo(f"{'='*60}")
        click.echo(f"  Topic:    {topic}")
        click.echo(f"  Category: {category}")
        click.echo(f"  Type:     {content_type}")
        click.echo(f"  Style:    {style}")
        click.echo(f"  Duration: {duration}s")
        click.echo(f"{'='*60}\n")

        crew = CreativeCrew()
        brief = await crew.produce(
            topic=topic,
            category=category,
            content_type=content_type,
            style_preset=style,
            duration=duration,
        )

        # Display agent results
        click.echo(f"\n  Agent Results:")
        click.echo(f"  {'─'*50}")
        click.echo(f"  Approved:      {brief.approved}")
        click.echo(f"  Quality:       {brief.quality_scores}")
        click.echo(f"  Mood:          {brief.mood}")
        click.echo(f"  Lighting:      {brief.lighting_setup[:60]}...")
        click.echo(f"  Colors:        {brief.color_palette[:3]}")
        click.echo(f"  Hook:          {brief.hook_line}")
        click.echo(f"  CTA:           {brief.cta}")
        click.echo(f"  Hashtags:      {len(brief.hashtags)} tags")
        click.echo(f"  Pacing:        {brief.pacing}")
        click.echo(f"  Music mood:    {brief.music_mood}")
        if brief.voiceover_text:
            click.echo(f"  Voiceover:     {brief.voiceover_text[:60]}...")
        click.echo(f"  Image prompt:  {brief.image_prompt[:80]}...")
        click.echo(f"  {'─'*50}")

        if dry_run:
            click.echo("\n  [DRY RUN] Skipping generation and posting.")
            click.echo(f"\n  Full caption:\n{brief.caption}")
            return

        if not brief.approved:
            click.echo("\n  Content did not pass quality review.")
            click.echo(f"  Revision notes: {brief.revision_notes}")
            click.echo("  Publishing anyway (override)...")

        # Phase 2: Generate and publish via pipeline
        click.echo(f"\n  Generating and publishing...")
        request_data = crew.brief_to_content_request(brief)
        request = ContentRequest(**request_data)

        pipeline = ContentPipeline()
        try:
            result = await pipeline.run(request)
            click.echo(f"\n  Result:")
            click.echo(f"  Status:    {result.status}")
            click.echo(f"  Request:   {result.request_id}")
            if result.media_id:
                click.echo(f"  Media ID:  {result.media_id}")
            if result.error:
                click.echo(f"  Error:     {result.error}", err=True)
        finally:
            await pipeline.close()

    asyncio.run(_run())


# =====================================================================
# generate command (template-based)
# =====================================================================


@cli.command()
@click.option("--template", "-t", required=True, help="Template name to use")
@click.option("--dry-run", is_flag=True, help="Generate without posting to Instagram")
@click.option(
    "--output-dir", "-o",
    type=click.Path(),
    default=None,
    help="Custom output directory",
)
@click.option("--caption", "-c", default=None, help="Override caption text")
@click.option("--voiceover", "-v", default=None, help="Override voiceover text (Uzbek)")
def generate(
    template: str,
    dry_run: bool,
    output_dir: str | None,
    caption: str | None,
    voiceover: str | None,
):
    """Generate content from a template and optionally post to Instagram."""
    from pipeline.orchestrator import ContentPipeline, ContentRequest
    from templates.prompts import get_template_by_name

    tmpl = get_template_by_name(template)
    if not tmpl:
        click.echo(f"Template '{template}' not found. Use 'templates' to list.", err=True)
        sys.exit(1)

    if output_dir:
        settings.content_output_dir = Path(output_dir)

    request = ContentRequest(
        content_type=tmpl.content_type,
        image_prompt=tmpl.image_prompt,
        caption=caption or tmpl.caption,
        voiceover_text=voiceover or tmpl.voiceover_text,
        image_style=tmpl.image_style,
        video_duration=tmpl.video_duration,
        subtitle_text=tmpl.subtitle_text,
        carousel_prompts=tmpl.carousel_prompts,
        hashtags=tmpl.hashtags,
    )

    async def _run():
        pipeline = ContentPipeline()
        try:
            if dry_run:
                click.echo(f"[DRY RUN] Generating content: {template}")
                click.echo(f"  Type: {request.content_type}")
                click.echo(f"  Image prompt: {request.image_prompt[:80]}...")
                if request.voiceover_text:
                    click.echo(f"  Voiceover: {request.voiceover_text[:80]}...")
                click.echo(f"  Caption: {request.caption[:80]}...")
                click.echo("  Skipping actual generation and posting.")
                return

            click.echo(f"Generating content: {template}...")
            result = await pipeline.run(request)

            click.echo(f"\nResult:")
            click.echo(f"  Status: {result.status}")
            click.echo(f"  Request ID: {result.request_id}")
            if result.media_id:
                click.echo(f"  Instagram Media ID: {result.media_id}")
            if result.local_paths:
                click.echo(f"  Local files: {', '.join(result.local_paths)}")
            if result.error:
                click.echo(f"  Error: {result.error}", err=True)
        finally:
            await pipeline.close()

    asyncio.run(_run())


# =====================================================================
# schedule command
# =====================================================================


@cli.command()
@click.option(
    "--times", "-t",
    default=None,
    help="Comma-separated posting times (HH:MM), e.g. '09:00,13:00,18:00'",
)
@click.option(
    "--timezone", "-tz",
    default=None,
    help="Timezone (default: Asia/Tashkent)",
)
def schedule(times: str | None, timezone: str | None):
    """Start the automated content scheduler."""
    from scheduler import ContentScheduler

    post_times = times.split(",") if times else None

    click.echo("Starting Instagram Content Scheduler...")
    click.echo(f"  Post times: {post_times or 'default (09:00, 13:00, 18:00)'}")
    click.echo(f"  Timezone: {timezone or settings.timezone}")
    click.echo("  Press Ctrl+C to stop.\n")

    scheduler = ContentScheduler(
        post_times=post_times,
        timezone=timezone,
    )
    asyncio.run(scheduler.start())


# =====================================================================
# templates command
# =====================================================================


@cli.command()
@click.option("--name", "-n", default=None, help="Show details for a specific template")
@click.option("--category", "-c", default=None, help="Filter by category")
def templates(name: str | None, category: str | None):
    """List available content templates."""
    from templates.prompts import (
        TEMPLATES,
        get_template_by_name,
        get_templates_by_category,
    )

    if name:
        tmpl = get_template_by_name(name)
        if not tmpl:
            click.echo(f"Template '{name}' not found.", err=True)
            sys.exit(1)
        click.echo(f"\nTemplate: {tmpl.name}")
        click.echo(f"  Category: {tmpl.category}")
        click.echo(f"  Type: {tmpl.content_type}")
        click.echo(f"  Style: {tmpl.image_style}")
        click.echo(f"\n  Image Prompt:\n    {tmpl.image_prompt}")
        if tmpl.voiceover_text:
            click.echo(f"\n  Voiceover (UZ):\n    {tmpl.voiceover_text}")
        click.echo(f"\n  Caption:\n    {tmpl.caption}")
        if tmpl.hashtags:
            click.echo(f"\n  Hashtags: {' '.join('#' + h for h in tmpl.hashtags)}")
        if tmpl.carousel_prompts:
            click.echo(f"\n  Carousel slides: {len(tmpl.carousel_prompts)}")
            for i, p in enumerate(tmpl.carousel_prompts, 1):
                click.echo(f"    {i}. {p[:70]}...")
        return

    templates_list = (
        get_templates_by_category(category) if category else TEMPLATES
    )

    if not templates_list:
        click.echo(f"No templates found for category '{category}'.", err=True)
        sys.exit(1)

    click.echo(f"\nAvailable templates ({len(templates_list)}):\n")
    click.echo(f"  {'Name':<25} {'Type':<12} {'Category':<15} {'Has Voice'}")
    click.echo(f"  {'-'*25} {'-'*12} {'-'*15} {'-'*10}")
    for t in templates_list:
        has_voice = "Yes" if t.voiceover_text else "No"
        click.echo(f"  {t.name:<25} {t.content_type:<12} {t.category:<15} {has_voice}")

    click.echo(f"\nCategories: motivational, educational, product, lifestyle, ")
    click.echo(f"            recipe, travel, tech, fashion, humor")
    click.echo(f"\nUse --name <template> to see details.")


# =====================================================================
# history command
# =====================================================================


@cli.command()
@click.option("--limit", "-l", default=20, help="Number of recent posts to show")
def history(limit: int):
    """Show posting history."""
    history_file = Path(settings.content_output_dir) / "post_history.json"

    if not history_file.exists():
        click.echo("No posting history yet.")
        return

    records = json.loads(history_file.read_text())
    recent = records[-limit:]

    click.echo(f"\nRecent posts ({len(recent)} of {len(records)}):\n")
    click.echo(f"  {'Timestamp':<22} {'Template':<25} {'Type':<10} {'Status'}")
    click.echo(f"  {'-'*22} {'-'*25} {'-'*10} {'-'*10}")
    for r in reversed(recent):
        ts = r["timestamp"][:19]
        click.echo(
            f"  {ts:<22} {r['template']:<25} {r['content_type']:<10} {r['status']}"
        )


# =====================================================================
# strategy command
# =====================================================================


@cli.command()
@click.option("--plan-week", is_flag=True, help="Plan a full week of content")
@click.option("--plan-day", is_flag=True, help="Plan today's content")
@click.option("--posts-per-day", "-p", default=3, help="Posts per day (1-5)")
def strategy(plan_week: bool, plan_day: bool, posts_per_day: int):
    """Content strategy planning and calendar management."""
    from strategy.engine import StrategyEngine
    from strategy.calendar import ContentCalendar

    engine = StrategyEngine()
    calendar = ContentCalendar()

    if plan_week:
        slots = engine.plan_week(posts_per_day)
        calendar.set_slots(slots)
        calendar.save()
        click.echo(calendar.display())
    elif plan_day:
        slots = engine.plan_day(posts_per_day)
        calendar.set_slots(slots)
        click.echo(calendar.display())
    else:
        # Show existing calendar
        calendar.load()
        click.echo(calendar.display())

        # Show next slot
        next_slot = calendar.get_next_slot()
        if next_slot:
            click.echo(
                f"\n  Next post: {next_slot.day} {next_slot.time} — "
                f"{next_slot.category}/{next_slot.content_type}: {next_slot.topic}"
            )


# =====================================================================
# analytics command
# =====================================================================


@cli.command()
@click.option("--report", "-r", is_flag=True, help="Full analytics report")
@click.option("--suggest", "-s", is_flag=True, help="Get content suggestions")
def analytics(report: bool, suggest: bool):
    """View content performance analytics."""
    from skills.analytics import AnalyticsSkills

    if report or not suggest:
        click.echo(AnalyticsSkills.generate_report())

    if suggest:
        suggestion = AnalyticsSkills.suggest_next_content()
        click.echo(f"\n  Content Suggestion:")
        click.echo(f"  {'─'*40}")
        click.echo(f"  Category: {suggestion['recommended_category']}")
        click.echo(f"  Type:     {suggestion['recommended_type']}")
        click.echo(f"  Reason:   {suggestion['reasoning']}")


# =====================================================================
# queue command
# =====================================================================


@cli.command()
@click.option("--add", "-a", is_flag=True, help="Add item to queue")
@click.option("--topic", "-t", default=None, help="Content topic")
@click.option("--category", "-c", default=None, help="Content category")
@click.option("--content-type", "-ct", default="reel")
@click.option("--priority", "-p", default=5, type=int, help="Priority 1-10")
@click.option("--from-calendar", is_flag=True, help="Enqueue from weekly calendar")
@click.option("--process", is_flag=True, help="Process next item in queue")
def queue(
    add: bool,
    topic: str | None,
    category: str | None,
    content_type: str,
    priority: int,
    from_calendar: bool,
    process: bool,
):
    """Manage the content publication queue."""
    from pipeline.queue import ContentQueue

    q = ContentQueue()

    if add and topic and category:
        item = q.enqueue(topic, category, content_type, priority=priority)
        click.echo(f"  Queued: {item.id} — {topic} [{category}] P{priority}")

    elif from_calendar:
        from strategy.engine import StrategyEngine
        engine = StrategyEngine()
        slots = engine.plan_week()
        items = q.enqueue_from_calendar(slots)
        click.echo(f"  Enqueued {len(items)} items from weekly calendar.")

    elif process:
        item = q.dequeue()
        if not item:
            click.echo("  Queue is empty or no items ready.")
            return

        click.echo(f"  Processing: {item.id} — {item.topic}")

        async def _process():
            from agents.crew import CreativeCrew
            from pipeline.orchestrator import ContentPipeline, ContentRequest

            crew = CreativeCrew()
            brief = await crew.produce(
                topic=item.topic,
                category=item.category,
                content_type=item.content_type,
                style_preset=item.style_preset,
                duration=item.duration,
            )
            request = ContentRequest(**crew.brief_to_content_request(brief))
            pipeline = ContentPipeline()
            try:
                result = await pipeline.run(request)
                if result.status == "published":
                    q.mark_published(item.id, result.media_id)
                    click.echo(f"  Published! Media ID: {result.media_id}")
                else:
                    q.mark_failed(item.id, result.error)
                    click.echo(f"  Failed: {result.error}", err=True)
            finally:
                await pipeline.close()

        asyncio.run(_process())
    else:
        click.echo(q.display())


# =====================================================================
# ab-test command
# =====================================================================


@cli.command("ab-test")
@click.option("--topic", "-t", required=True, help="Content topic")
@click.option("--category", "-c", required=True, help="Content category")
@click.option("--strategy", "-s", default="visual_style",
              type=click.Choice(["visual_style", "hook_style", "pacing", "duration"]))
@click.option("--variants", "-v", default=2, type=int, help="Number of variants (2-3)")
@click.option("--dry-run", is_flag=True, help="Preview without generating")
def ab_test(topic: str, category: str, strategy: str, variants: int, dry_run: bool):
    """Create an A/B test experiment with multiple content variants."""
    from pipeline.ab_testing import ABTestingEngine, VARIATION_STRATEGIES

    if dry_run:
        strat = VARIATION_STRATEGIES.get(strategy, {})
        click.echo(f"\n  A/B Test Preview:")
        click.echo(f"  Strategy: {strategy} — {strat.get('description', '')}")
        click.echo(f"  Topic: {topic}")
        click.echo(f"  Variants: {variants}")
        for i, var in enumerate(strat.get("variations", [])[:variants]):
            click.echo(f"    Variant {i+1}: {var.get('name', '?')}")
        return

    async def _run():
        engine = ABTestingEngine()
        exp = await engine.create_experiment(
            topic=topic,
            category=category,
            strategy=strategy,
            variant_count=variants,
        )
        click.echo(f"\n  Experiment created: {exp.id}")
        click.echo(f"  Variants: {len(exp.variants)}")
        for v in exp.variants:
            click.echo(f"    {v.name} ({v.id})")
        click.echo(f"\n  Publish variants and track with:")
        click.echo(f"    Metrics will be collected via webhook.")

    asyncio.run(_run())


# =====================================================================
# webhook command
# =====================================================================


@cli.command()
@click.option("--port", "-p", default=8080, help="Webhook server port")
def webhook(port: int):
    """Start the webhook server for Instagram insights and triggers."""
    from webhook import start_webhook_server

    click.echo(f"Starting webhook server on port {port}...")
    click.echo(f"  Endpoints:")
    click.echo(f"    GET  /health            — Health check")
    click.echo(f"    GET  /status            — Queue & scheduler status")
    click.echo(f"    GET  /queue             — View content queue")
    click.echo(f"    GET  /calendar          — View content calendar")
    click.echo(f"    GET  /analytics         — Analytics report")
    click.echo(f"    POST /webhook/instagram — Instagram webhook")
    click.echo(f"    POST /trigger/generate  — Trigger content generation")
    click.echo(f"  Press Ctrl+C to stop.\n")

    asyncio.run(start_webhook_server(port))


if __name__ == "__main__":
    cli()
