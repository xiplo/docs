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
from utils.logging import setup_logging

# Configure structured logging (auto-detects JSON mode via LOG_FORMAT env)
setup_logging(log_level=settings.log_level)

logger = structlog.get_logger(__name__)


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Instagram Content Generator — Multi-Agent Creative System

    Nano Banana (images) + Kling 3.0 (video) + Eleven Labs (Uzbek TTS)
    """
    pass


# =====================================================================
# doctor command (startup diagnostics)
# =====================================================================


@cli.command()
@click.option("--strict", is_flag=True, help="Require all API keys")
def doctor(strict: bool):
    """Run startup diagnostics and validate environment."""
    from utils.startup import validate_environment

    report = validate_environment(require_all=strict)
    click.echo(report.display())

    if not report.passed:
        sys.exit(1)


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
    click.echo(f"    GET  /trends            — Trending topics")
    click.echo(f"    GET  /review            — Content review queue")
    click.echo(f"    POST /webhook/instagram — Instagram webhook")
    click.echo(f"    POST /trigger/generate  — Trigger content generation")
    click.echo(f"    POST /trigger/trends    — Auto-enqueue trending topics")
    click.echo(f"    POST /review/approve/ID — Approve content for publishing")
    click.echo(f"    POST /review/reject/ID  — Reject content")
    click.echo(f"  Press Ctrl+C to stop.\n")

    asyncio.run(start_webhook_server(port))


# =====================================================================
# trends command
# =====================================================================


@cli.command()
@click.option("--category", "-c", default=None, help="Filter by category")
@click.option("--hashtags", is_flag=True, help="Show trending hashtags")
@click.option("--plan", is_flag=True, help="Create content plan from trends")
def trends(category: str | None, hashtags: bool, plan: bool):
    """Show trending topics and seasonal content opportunities."""
    from strategy.trends import TrendEngine

    if hashtags:
        tags = TrendEngine.get_trending_hashtags(category or "")
        click.echo(f"\n  Trending hashtags:")
        click.echo(f"  {' '.join('#' + t for t in tags[:25])}")
        return

    if plan:
        from pipeline.queue import ContentQueue
        trends_list = TrendEngine.get_current_trends(limit=5)
        q = ContentQueue()
        for trend in trends_list:
            suggestion = TrendEngine.suggest_content_for_trend(trend)
            q.enqueue(
                topic=suggestion["topic"],
                category=suggestion["category"],
                content_type=suggestion["content_type"],
                priority=suggestion["priority"],
            )
        click.echo(f"  Enqueued {len(trends_list)} trending topics to queue.")
        click.echo(q.display())
        return

    click.echo(TrendEngine.display_trends())


# =====================================================================
# recycle command
# =====================================================================


@cli.command()
@click.option("--strategy", "-s", default="new_angle",
              type=click.Choice(["reel_to_carousel", "reel_to_story", "image_to_reel", "new_angle"]))
@click.option("--generate", is_flag=True, help="Generate recycled content")
@click.option("--limit", "-l", default=5, help="Number of candidates")
def recycle(strategy: str, generate: bool, limit: int):
    """Find and repurpose top-performing content."""
    from strategy.recycler import ContentRecycler

    recycler = ContentRecycler()

    if generate:
        candidates = recycler.find_candidates(strategy=strategy, limit=1)
        if not candidates:
            click.echo("  No recyclable content found.")
            return

        candidate = candidates[0]
        request = recycler.create_recycled_request(candidate)
        click.echo(f"  Recycling: {candidate.topic}")
        click.echo(f"  Strategy: {strategy} ({candidate.content_type} → {request.content_type})")
        click.echo(f"  Original score: {candidate.score:.1f}/10")

        from pipeline.queue import ContentQueue
        q = ContentQueue()
        q.enqueue(
            topic=candidate.topic,
            category=candidate.category,
            content_type=request.content_type,
            priority=8,
        )
        click.echo("  Added to queue with priority 8.")
    else:
        click.echo(recycler.get_recycle_report())


# =====================================================================
# accounts command
# =====================================================================


@cli.command()
@click.option("--add", "-a", is_flag=True, help="Add a new account")
@click.option("--id", "account_id", default=None, help="Account ID")
@click.option("--name", default=None, help="Account display name")
@click.option("--deactivate", is_flag=True, help="Deactivate an account")
def accounts(add: bool, account_id: str | None, name: str | None, deactivate: bool):
    """Manage multiple Instagram accounts."""
    from accounts import AccountManager, AccountConfig

    manager = AccountManager()

    if add and account_id and name:
        config = AccountConfig(id=account_id, name=name)
        try:
            manager.add_account(config)
            click.echo(f"  Account '{account_id}' ({name}) added.")
        except ValueError as e:
            click.echo(f"  Error: {e}", err=True)
    elif deactivate and account_id:
        if manager.deactivate_account(account_id):
            click.echo(f"  Account '{account_id}' deactivated.")
        else:
            click.echo(f"  Account '{account_id}' not found.", err=True)
    else:
        click.echo(manager.display())


# =====================================================================
# moderate command
# =====================================================================


@cli.command()
@click.option("--text", "-t", required=True, help="Text to moderate")
@click.option("--hashtags", "-h", default="", help="Comma-separated hashtags")
def moderate(text: str, hashtags: str):
    """Check content against moderation rules."""
    from skills.moderation import ContentModerator

    tags = [t.strip() for t in hashtags.split(",") if t.strip()] if hashtags else []
    result = ContentModerator.check_content_request(text, tags)

    click.echo(f"\n  Moderation: {result.summary}")
    if result.flags:
        click.echo(f"  Flags:")
        for flag in result.flags:
            click.echo(f"    - {flag}")
    if result.suggestions:
        click.echo(f"  Suggestions:")
        for s in result.suggestions:
            click.echo(f"    - {s}")


# =====================================================================
# status command
# =====================================================================


@cli.command()
def status():
    """Show system status — circuit breakers, rate limits, queue."""
    from utils.circuit_breaker import CIRCUIT_BREAKERS
    from utils.rate_limiter import RATE_LIMITERS

    click.echo("\n  Circuit Breakers:")
    for name, breaker in CIRCUIT_BREAKERS.items():
        s = breaker.get_status()
        click.echo(f"    {name:<15} {s['state']:<10} failures={s['failures']}")

    click.echo(f"\n  Rate Limiters:")
    for name, limiter in RATE_LIMITERS.items():
        click.echo(f"    {name:<15} {limiter.rate:.2f} req/s  burst={limiter.capacity}")

    from pipeline.queue import ContentQueue
    q = ContentQueue()
    stats = q.get_stats()
    click.echo(f"\n  Queue: {', '.join(f'{k}={v}' for k, v in stats.items())}")

    # Token status
    try:
        from utils.token_refresh import TokenRefresher
        refresher = TokenRefresher()
        ts = refresher.get_status()
        click.echo(f"\n  Instagram Token:")
        click.echo(f"    Configured: {ts['configured']}")
        click.echo(f"    Expires: {ts['expires_at']}")
        click.echo(f"    Days remaining: {ts['days_remaining']}")
        if ts['needs_refresh']:
            click.echo(f"    WARNING: Token needs refresh!")
    except Exception:
        pass


# =====================================================================
# batch command
# =====================================================================


@cli.command()
@click.option("--from-queue", is_flag=True, help="Process items from queue")
@click.option("--limit", "-l", default=10, help="Max items to process")
@click.option("--concurrency", "-c", default=1, help="Parallel workers (1=sequential)")
def batch(from_queue: bool, limit: int, concurrency: int):
    """Batch process multiple content items."""
    from pipeline.batch import BatchProcessor

    processor = BatchProcessor(concurrency=concurrency)

    if from_queue:
        click.echo(f"  Batch processing up to {limit} items from queue...")
        click.echo(f"  Concurrency: {concurrency}")

        async def _run():
            result = await processor.process_queue(limit=limit)
            click.echo(result.display())

        asyncio.run(_run())
    else:
        click.echo("  Use --from-queue to process queue items.")
        click.echo("  Example: python main.py batch --from-queue -l 5 -c 2")


# =====================================================================
# review command
# =====================================================================


@cli.command()
@click.option("--pending", is_flag=True, help="Show pending items only")
@click.option("--approve", default=None, help="Approve item by ID")
@click.option("--reject", default=None, help="Reject item by ID")
@click.option("--notes", "-n", default="", help="Reviewer notes")
def review(pending: bool, approve: str | None, reject: str | None, notes: str):
    """Manage content approval workflow."""
    from pipeline.approval import ApprovalWorkflow

    wf = ApprovalWorkflow()

    if approve:
        item = wf.approve(approve, notes)
        if item:
            click.echo(f"  Approved: {approve}")
            # Auto-enqueue approved content
            from pipeline.queue import ContentQueue
            q = ContentQueue()
            q.enqueue(
                topic=item.topic,
                category=item.category,
                content_type=item.content_type,
                priority=9,
            )
            click.echo("  Added to queue with priority 9.")
        else:
            click.echo(f"  Item {approve} not found or not pending.", err=True)
    elif reject:
        item = wf.reject(reject, notes)
        if item:
            click.echo(f"  Rejected: {reject}")
        else:
            click.echo(f"  Item {reject} not found or not pending.", err=True)
    else:
        filter_status = "pending" if pending else ""
        click.echo(wf.display(status_filter=filter_status))


# =====================================================================
# token command
# =====================================================================


@cli.command()
@click.option("--refresh", is_flag=True, help="Force token refresh")
@click.option("--check", is_flag=True, help="Check token validity")
def token(refresh: bool, check: bool):
    """Manage Instagram access token lifecycle."""
    from utils.token_refresh import TokenRefresher

    refresher = TokenRefresher()

    if refresh:
        async def _refresh():
            new_token = await refresher.refresh()
            click.echo(f"  Token refreshed: {new_token[:10]}...{new_token[-5:]}")

        asyncio.run(_refresh())
    elif check:
        async def _check():
            token_val = await refresher.check_and_refresh()
            if token_val:
                click.echo(f"  Token valid: {token_val[:10]}...{token_val[-5:]}")
            else:
                click.echo("  Token not configured.", err=True)

        asyncio.run(_check())
    else:
        status = refresher.get_status()
        click.echo(f"\n  Instagram Token Status:")
        click.echo(f"    Configured: {status['configured']}")
        click.echo(f"    Expires: {status['expires_at']}")
        click.echo(f"    Days remaining: {status['days_remaining']}")
        click.echo(f"    Needs refresh: {status['needs_refresh']}")


# =====================================================================
# notify command
# =====================================================================


@cli.command()
@click.option("--test", is_flag=True, help="Send a test notification")
@click.option("--message", "-m", default="", help="Custom message")
def notify(test: bool, message: str):
    """Test notification channels (Telegram, webhook)."""
    from notifications import NotificationManager

    manager = NotificationManager()
    click.echo(f"  Telegram: {'enabled' if manager.telegram_enabled else 'disabled'}")
    click.echo(f"  Webhook:  {'enabled' if manager.webhook_enabled else 'disabled'}")

    if test or message:
        msg = message or "Test notification from Instagram Content Generator"

        async def _send():
            await manager.send(msg)
            click.echo(f"  Sent: {msg[:60]}")

        asyncio.run(_send())


# =====================================================================
# hashtags command
# =====================================================================


@cli.command()
@click.option("--category", "-c", default="", help="Category (motivational, recipe, travel, ...)")
@click.option("--count", "-n", default=12, help="Number of hashtags to suggest")
@click.option("--check", default="", help="Comma-separated tags to check for bans")
def hashtags(category: str, count: int, check: str):
    """Research and suggest optimal hashtags."""
    from skills.hashtags import HashtagResearch

    if check:
        tags = [t.strip() for t in check.split(",")]
        banned = HashtagResearch.check_banned(tags)
        if banned:
            click.echo(f"  Banned/risky hashtags: {', '.join(banned)}")
        else:
            click.echo("  All hashtags are safe.")
        return

    if category:
        result = HashtagResearch.suggest(category, count=count)
        click.echo(f"\n  Suggested for '{category}' ({result.total} tags):")
        click.echo(f"  {result.as_string()}")
        click.echo(f"\n  Breakdown: {result.broad_count} broad / {result.mid_count} mid / {result.niche_count} niche")
        if result.banned_removed:
            click.echo(f"  Removed: {', '.join(result.banned_removed)}")
    else:
        click.echo(HashtagResearch.display())


# =====================================================================
# backup command
# =====================================================================


@cli.command()
@click.option("--create", is_flag=True, help="Create a backup")
@click.option("--restore", default="", help="Restore from backup name")
@click.option("--label", "-l", default="", help="Label for backup")
def backup(create: bool, restore: str, label: str):
    """Backup and restore data files."""
    from utils.backup import BackupManager

    mgr = BackupManager()

    if create:
        path = mgr.create_backup(label=label)
        click.echo(f"  Backup created: {path.name}")
    elif restore:
        count = mgr.restore_backup(restore)
        if count:
            click.echo(f"  Restored {count} files from '{restore}'")
        else:
            click.echo(f"  Backup '{restore}' not found.", err=True)
    else:
        click.echo(mgr.display())


# =====================================================================
# metrics command
# =====================================================================


@cli.command()
@click.option("--prometheus", is_flag=True, help="Export in Prometheus format")
@click.option("--json", "as_json", is_flag=True, help="Export as JSON")
def metrics(prometheus: bool, as_json: bool):
    """View system metrics."""
    from utils.metrics import metrics as m

    if prometheus:
        click.echo(m.export_prometheus())
    elif as_json:
        import json
        click.echo(json.dumps(m.get_all(), indent=2))
    else:
        click.echo(m.display())


# =====================================================================
# library command
# =====================================================================


@cli.command()
@click.option("--category", "-c", default="", help="Filter by category")
@click.option("--use", default="", help="Use template by name (generate content)")
def library(category: str, use: str):
    """Browse and use pre-built content templates."""
    from templates.library import TemplateLibrary

    if use:
        tmpl = TemplateLibrary.get_by_name(use)
        if not tmpl:
            click.echo(f"  Template '{use}' not found.", err=True)
            return

        rendered = tmpl.render()
        click.echo(f"\n  Template: {tmpl.name}")
        click.echo(f"  Topic: {rendered['topic']}")
        click.echo(f"  Type: {rendered['content_type']}")
        click.echo(f"  Caption: {rendered['caption'][:80]}...")
        click.echo(f"  Hashtags: {', '.join(rendered['hashtags'])}")

        if click.confirm("  Enqueue this for generation?"):
            from pipeline.queue import ContentQueue
            q = ContentQueue()
            item = q.enqueue(
                topic=rendered["topic"],
                category=rendered["category"],
                content_type=rendered["content_type"],
                priority=7,
            )
            click.echo(f"  Queued: {item.id}")
    else:
        click.echo(TemplateLibrary.display(category))


# =====================================================================
# dashboard command
# =====================================================================


@cli.command()
def dashboard():
    """Show live system dashboard — all subsystems at a glance."""
    from utils.dashboard import Dashboard
    click.echo(Dashboard.render())


# =====================================================================
# plugins command
# =====================================================================


@cli.command()
@click.option("--load", is_flag=True, help="Discover and load plugins")
def plugins(load: bool):
    """View and manage pipeline plugins."""
    from plugins import plugin_registry

    if load:
        count = plugin_registry.load_plugins()
        click.echo(f"  Loaded {count} plugin(s).")

    click.echo(plugin_registry.display())


# =====================================================================
# validate command
# =====================================================================


@cli.command()
@click.argument("path")
@click.option("--type", "content_type", default="image", help="Content type (image/reel/story)")
def validate(path: str, content_type: str):
    """Validate media files against Instagram requirements."""
    from pathlib import Path as P
    from utils.media_validator import MediaValidator

    file_path = P(path)
    result = MediaValidator.validate_for_pipeline(file_path, content_type)

    if result.valid:
        click.echo(f"  VALID — {content_type}")
    else:
        click.echo(f"  INVALID — {content_type}")

    for key, val in result.metadata.items():
        click.echo(f"    {key}: {val}")

    for err in result.errors:
        click.echo(f"    ERROR: {err}")

    for warn in result.warnings:
        click.echo(f"    WARNING: {warn}")


# =====================================================================
# content command (CMS)
# =====================================================================


@cli.command()
@click.option("--create", is_flag=True, help="Create new content item")
@click.option("--list", "list_all", is_flag=True, help="List all content")
@click.option("--status", "filter_status", default="", help="Filter by status")
@click.option("--search", "query", default="", help="Search content")
@click.option("--title", default="", help="Content title")
@click.option("--topic", "-t", default="", help="Topic")
@click.option("--category", "-c", default="", help="Category")
@click.option("--type", "content_type", default="reel", help="Content type")
@click.option("--submit", default="", help="Submit item for review (by ID)")
@click.option("--approve", default="", help="Approve item (by ID)")
@click.option("--schedule-id", default="", help="Schedule item (by ID)")
@click.option("--platforms", default="", help="Target platforms (comma-separated)")
@click.option("--archive", default="", help="Archive item (by ID)")
def content(
    create, list_all, filter_status, query, title, topic, category,
    content_type, submit, approve, schedule_id, platforms, archive,
):
    """Content management system — full lifecycle."""
    from cms.content_manager import ContentManager

    cm = ContentManager()

    if create:
        item = cm.create(
            title=title or topic,
            topic=topic,
            category=category,
            content_type=content_type,
        )
        click.echo(f"  Created: {item.id} ({item.status})")
    elif submit:
        cm.submit_for_review(submit)
        click.echo(f"  Submitted for review: {submit}")
    elif approve:
        cm.approve(approve)
        click.echo(f"  Approved: {approve}")
    elif schedule_id:
        plats = [p.strip() for p in platforms.split(",")] if platforms else ["instagram"]
        cm.schedule(schedule_id, datetime.now().isoformat(), plats)
        click.echo(f"  Scheduled: {schedule_id} → {', '.join(plats)}")
    elif archive:
        cm.archive(archive)
        click.echo(f"  Archived: {archive}")
    elif query:
        results = cm.search(query)
        for r in results:
            click.echo(f"  {r.id} [{r.status}] {r.title or r.topic}")
    else:
        click.echo(cm.display(status_filter=filter_status))


# =====================================================================
# crosspost command
# =====================================================================


@cli.command()
@click.option("--content-id", default="", help="CMS content ID to cross-post")
@click.option("--platforms", "-p", default="", help="Platforms (comma-separated)")
@click.option("--rules", is_flag=True, help="Show publishing rules")
@click.option("--route", is_flag=True, help="Show platform routing for content")
def crosspost(content_id, platforms, rules, route):
    """Cross-post content to multiple social platforms."""
    if rules:
        from cms.publisher import PublishingRouter
        router = PublishingRouter()
        click.echo(router.display())
        return

    if route:
        from cms.publisher import PublishingRouter
        from cms.content_manager import ContentManager

        router = PublishingRouter()
        if content_id:
            cm = ContentManager()
            item = cm.get(content_id)
            if item:
                target = router.get_platforms({
                    "content_type": item.content_type,
                    "category": item.category,
                    "campaign_id": item.campaign_id,
                    "tags": item.tags,
                })
                click.echo(f"  Content {content_id} → {', '.join(target)}")
            else:
                click.echo(f"  Content {content_id} not found.", err=True)
        return

    if content_id:
        from cms.content_manager import ContentManager
        from cms.cross_poster import CrossPoster, PlatformAdapter
        from cms.publisher import PublishingRouter

        cm = ContentManager()
        item = cm.get(content_id)
        if not item:
            click.echo(f"  Content {content_id} not found.", err=True)
            return

        if platforms:
            plats = [p.strip() for p in platforms.split(",")]
        else:
            router = PublishingRouter()
            plats = router.get_platforms({
                "content_type": item.content_type,
                "category": item.category,
            })

        click.echo(f"  Cross-posting {content_id} → {', '.join(plats)}")

        async def _crosspost():
            poster = CrossPoster()
            try:
                results = await poster.publish_multi(
                    {
                        "caption": item.caption,
                        "hashtags": item.hashtags,
                        "content_type": item.content_type,
                        "cdn_urls": item.cdn_urls,
                        "media_paths": item.media_paths,
                        "voiceover_text": item.voiceover_text,
                        "topic": item.topic,
                    },
                    plats,
                )
                for p, r in results.items():
                    status = r.get("status", "?")
                    click.echo(f"    {p}: {status}")
                cm.mark_published(content_id, results)
            finally:
                await poster.close()

        asyncio.run(_crosspost())
    else:
        click.echo("  Use --content-id to cross-post, --rules to view rules, --route to check routing.")


# =====================================================================
# campaign command
# =====================================================================


@cli.command()
@click.option("--create", is_flag=True, help="Create a campaign")
@click.option("--name", default="", help="Campaign name")
@click.option("--platforms", default="", help="Target platforms")
@click.option("--list", "list_all", is_flag=True, help="List campaigns")
@click.option("--complete", default="", help="Complete campaign (by ID)")
@click.option("--pause", default="", help="Pause campaign (by ID)")
def campaign(create, name, platforms, list_all, complete, pause):
    """Manage content campaigns."""
    from cms.campaigns import CampaignManager

    mgr = CampaignManager()

    if create:
        plats = [p.strip() for p in platforms.split(",")] if platforms else []
        c = mgr.create(name=name, target_platforms=plats)
        click.echo(f"  Campaign created: {c.id} — {c.name}")
    elif complete:
        mgr.complete(complete)
        click.echo(f"  Completed: {complete}")
    elif pause:
        mgr.pause(pause)
        click.echo(f"  Paused: {pause}")
    else:
        click.echo(mgr.display())


# =====================================================================
# assets command
# =====================================================================


@cli.command()
@click.option("--add", "add_path", default="", help="Add file to library")
@click.option("--tags", default="", help="Comma-separated tags")
@click.option("--search", "query", default="", help="Search assets")
@click.option("--unused", is_flag=True, help="Show unused assets")
def assets(add_path, tags, query, unused):
    """Manage media asset library."""
    from cms.asset_library import AssetLibrary

    lib = AssetLibrary()

    if add_path:
        tag_list = [t.strip() for t in tags.split(",")] if tags else []
        asset = lib.add(file_path=add_path, tags=tag_list)
        click.echo(f"  Added: {asset.id} ({asset.media_type}) {asset.name}")
    elif query:
        results = lib.search(query)
        for a in results:
            click.echo(f"  {a.id} [{a.media_type}] {a.name} ({', '.join(a.tags[:3])})")
    elif unused:
        results = lib.find_unused()
        click.echo(f"  Unused assets: {len(results)}")
        for a in results:
            click.echo(f"    {a.id} {a.name}")
    else:
        click.echo(lib.display())


# =====================================================================
# report command (cross-platform analytics)
# =====================================================================


@cli.command()
@click.option("--platforms", is_flag=True, help="Platform breakdown")
@click.option("--categories", is_flag=True, help="Category breakdown")
@click.option("--top", default=0, help="Show top N performers")
def report(platforms, categories, top):
    """Cross-platform analytics report."""
    from cms.analytics_aggregator import AnalyticsAggregator

    agg = AnalyticsAggregator()

    if platforms:
        summary = agg.get_platform_summary()
        for p, s in sorted(summary.items(), key=lambda x: x[1]["impressions"], reverse=True):
            click.echo(f"  {p:<12} posts={s['posts']}  reach={s['impressions']:,}  engagement={s['engagement']:,}")
    elif categories:
        cats = agg.get_category_performance()
        for cat, data in sorted(cats.items(), key=lambda x: x[1]["total_engagement"], reverse=True):
            click.echo(f"  {cat:<16} {data['posts']} posts  reach={data['total_impressions']:,}")
    elif top:
        best = agg.get_best_performing(top)
        for entry in best:
            click.echo(f"  {entry.content_id} eng={entry.total_engagement:,} best={entry.best_platform}")
    else:
        click.echo(agg.generate_report())


# =====================================================================
# optimizer command
# =====================================================================


@cli.command()
@click.option("--platform", "-p", default="", help="Specific platform")
@click.option("--schedule", is_flag=True, help="Generate optimized schedule")
@click.option("--posts-per-day", default=3, help="Posts per day (for schedule)")
def optimizer(platform, schedule, posts_per_day):
    """Find best posting times per platform."""
    from strategy.optimizer import EngagementOptimizer

    if schedule:
        platforms = [p.strip() for p in platform.split(",")] if platform else [
            "instagram", "tiktok", "youtube", "facebook", "telegram"
        ]
        sched = EngagementOptimizer.get_schedule(platforms, posts_per_day)
        click.echo("\n  Optimized Schedule:")
        for p, times in sched.items():
            click.echo(f"    {p:<12} {', '.join(times)}")
    elif platform:
        results = EngagementOptimizer.optimize(platform)
        for r in results:
            click.echo(f"\n  {r.platform.upper()} ({r.confidence})")
            click.echo(f"  Times: {', '.join(r.best_times[:3])}")
            click.echo(f"  Days:  {', '.join(r.best_days[:3])}")
    else:
        click.echo(EngagementOptimizer.display())


# =====================================================================
# localize command
# =====================================================================


@cli.command()
@click.option("--text", "-t", default="", help="Caption text (Uzbek)")
@click.option("--category", "-c", default="motivational", help="Category")
@click.option("--langs", default="uz,ru,en", help="Target languages")
@click.option("--info", is_flag=True, help="Show language profiles")
def localize(text, category, langs, info):
    """Generate multi-language captions."""
    from skills.localization import CaptionLocalizer

    if info:
        click.echo(CaptionLocalizer.display())
        return

    if not text:
        click.echo("  Provide --text to localize.")
        return

    target = [l.strip() for l in langs.split(",")]
    result = CaptionLocalizer.localize(text, category=category, target_langs=target)

    click.echo(f"\n  [uz] {result.uz}")
    if result.ru:
        click.echo(f"  [ru] {result.ru}")
    if result.en:
        click.echo(f"  [en] {result.en}")
    click.echo(f"\n  Hashtags UZ: {', '.join(result.hashtags_uz)}")
    click.echo(f"  Hashtags RU: {', '.join(result.hashtags_ru)}")
    click.echo(f"  Hashtags EN: {', '.join(result.hashtags_en)}")


# =====================================================================
# export/import commands
# =====================================================================


@cli.command(name="export")
@click.option("--output", "-o", default="", help="Output file path")
def export_data(output):
    """Export all data to a portable JSON archive."""
    from utils.export_import import DataExporter

    path = DataExporter.export_all(output)
    click.echo(f"  Exported to: {path}")
    click.echo(DataExporter.display_archive(str(path)))


@cli.command(name="import")
@click.argument("archive_path")
@click.option("--merge", is_flag=True, help="Merge with existing data (default: replace)")
def import_data(archive_path, merge):
    """Import data from a JSON archive."""
    from utils.export_import import DataExporter

    summary = DataExporter.import_all(archive_path, merge=merge)
    click.echo(f"\n  Imported: {len(summary['imported'])} sources")
    for item in summary["imported"]:
        click.echo(f"    + {item}")
    if summary["errors"]:
        click.echo(f"  Errors: {len(summary['errors'])}")
        for err in summary["errors"]:
            click.echo(f"    ! {err}")


# =====================================================================
# dedup command
# =====================================================================


@cli.command()
@click.option("--topic", "-t", default="", help="Check topic for duplicates")
@click.option("--similar", "-s", default="", help="Find similar content")
def dedup(topic, similar):
    """Check content for duplicates before publishing."""
    from skills.deduplication import DuplicateDetector

    if similar:
        results = DuplicateDetector.find_similar(similar)
        if results:
            for r in results:
                click.echo(f"  {r['similarity']:.0%}  {r['topic'][:50]}  ({r['posted']})")
        else:
            click.echo("  No similar content found.")
    elif topic:
        is_dup, reason = DuplicateDetector.is_duplicate(topic)
        if is_dup:
            click.echo(f"  DUPLICATE: {reason}")
        else:
            click.echo("  No duplicates found.")
    else:
        click.echo(DuplicateDetector.display())


# =====================================================================
# competitors command
# =====================================================================


@cli.command()
@click.option("--add", is_flag=True, help="Add a competitor")
@click.option("--name", default="", help="Competitor name")
@click.option("--platform", "-p", default="instagram", help="Platform")
@click.option("--handle", default="", help="Handle (@username)")
@click.option("--update", default="", help="Update metrics (competitor ID)")
@click.option("--followers", default=0, help="Follower count")
@click.option("--avg-likes", default=0, help="Average likes")
def competitors(add, name, platform, handle, update, followers, avg_likes):
    """Track competitor accounts."""
    from strategy.competitors import CompetitorTracker

    tracker = CompetitorTracker()

    if add:
        comp = tracker.add(name=name, platform=platform, handle=handle)
        click.echo(f"  Added: {comp.id} — {comp.name} ({comp.platform})")
    elif update:
        tracker.update_metrics(update, followers=followers, avg_likes=avg_likes)
        click.echo(f"  Updated: {update}")
    else:
        click.echo(tracker.display())


# =====================================================================
# versions command
# =====================================================================


@cli.command()
@click.option("--content-id", default="", help="Content ID to view versions")
@click.option("--diff", "diff_versions", default="", help="Compare versions (e.g., 1:2)")
def versions(content_id, diff_versions):
    """View content version history."""
    from cms.versioning import VersionManager
    import json as _json

    vm = VersionManager()

    if diff_versions and content_id:
        parts = diff_versions.split(":")
        if len(parts) == 2:
            changes = vm.diff(content_id, int(parts[0]), int(parts[1]))
            click.echo(f"\n  Diff v{parts[0]} → v{parts[1]}:")
            for field_name, change in changes.items():
                click.echo(f"    {field_name}: {change['from']} → {change['to']}")
    else:
        click.echo(vm.display(content_id))


# =====================================================================
# health command
# =====================================================================


@cli.command()
@click.option("--check", is_flag=True, help="Run health checks now")
@click.option("--critical", is_flag=True, help="Check only critical APIs")
def health(check, critical):
    """Monitor API provider health."""
    from utils.health import HealthMonitor

    if check or critical:
        async def _check():
            if critical:
                results = await HealthMonitor.check_critical()
            else:
                results = await HealthMonitor.check_all()
            click.echo(HealthMonitor.display(results))

        asyncio.run(_check())
    else:
        click.echo(HealthMonitor.display())


# =====================================================================
# ical command
# =====================================================================


@cli.command()
@click.option("--output", "-o", default="", help="Output .ics file path")
@click.option("--source", default="all", help="Source: cms, calendar, all")
def ical(output, source):
    """Export content schedule as iCal feed."""
    from utils.ical import CalendarFeed

    path = CalendarFeed.export_file(output, source)
    click.echo(f"  iCal exported: {path}")


# =====================================================================
# ai command (Claude-powered content generation)
# =====================================================================


@cli.command()
@click.option("--caption", is_flag=True, help="Generate AI caption")
@click.option("--script", is_flag=True, help="Generate AI video script")
@click.option("--review", is_flag=True, help="AI quality review")
@click.option("--translate", is_flag=True, help="AI translation")
@click.option("--topic", "-t", default="", help="Topic")
@click.option("--category", "-c", default="motivational", help="Category")
@click.option("--text", default="", help="Text to translate/review")
@click.option("--lang", default="ru", help="Target language")
def ai(caption, script, review, translate, topic, category, text, lang):
    """AI-powered content generation using Claude claude-sonnet-4-6."""
    from skills.ai_content import AIContentGenerator
    import json as _json

    gen = AIContentGenerator()
    if not gen.ai_enabled:
        click.echo("  AI mode: FALLBACK (set ANTHROPIC_API_KEY for Claude claude-sonnet-4-6)")
    else:
        click.echo("  AI mode: Claude claude-sonnet-4-6")

    async def _run():
        try:
            if caption:
                result = await gen.generate_caption(topic or "Uzbek lifestyle", category)
                click.echo(_json.dumps(result, indent=2, ensure_ascii=False))
            elif script:
                result = await gen.generate_script(topic or "Motivation", category)
                click.echo(_json.dumps(result, indent=2, ensure_ascii=False))
            elif review:
                result = await gen.review_content(text or "Test caption", category=category)
                click.echo(_json.dumps(result, indent=2, ensure_ascii=False))
            elif translate:
                result = await gen.translate(text or topic, target_lang=lang, category=category)
                click.echo(_json.dumps(result, indent=2, ensure_ascii=False))
            else:
                click.echo("  Use --caption, --script, --review, or --translate")
        finally:
            await gen.close()

    asyncio.run(_run())


# =====================================================================
# audience command (CRM)
# =====================================================================


@cli.command()
@click.option("--segments", is_flag=True, help="Show audience segments")
@click.option("--engagement", is_flag=True, help="Show engagement tracker")
@click.option("--funnel", is_flag=True, help="Show follower funnel")
@click.option("--for-content", default="", help="Find segments for category:type")
def audience(segments, engagement, funnel, for_content):
    """CRM — audience segments, engagement, funnel."""
    if engagement:
        from crm.engagement import EngagementTracker
        click.echo(EngagementTracker().display())
    elif funnel:
        from crm.funnel import FollowerFunnel
        click.echo(FollowerFunnel().display())
    elif for_content:
        from crm.audience import AudienceManager
        parts = for_content.split(":")
        cat = parts[0]
        ct = parts[1] if len(parts) > 1 else "reel"
        mgr = AudienceManager()
        matches = mgr.get_for_content(cat, ct)
        for s in matches:
            click.echo(f"  {s.id:<16} {s.name:<22} {', '.join(s.active_platforms[:3])}")
    else:
        from crm.audience import AudienceManager
        click.echo(AudienceManager().display())


if __name__ == "__main__":
    cli()
