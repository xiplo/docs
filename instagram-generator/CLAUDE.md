# Social Content CMS — CLAUDE.md

## Project overview

Full-stack content management system for multi-platform social media.
Auto-generates and cross-posts Uzbek-language content across 7 platforms:
Instagram, Twitter/X, TikTok, YouTube Shorts, Facebook, Telegram, LinkedIn.
Powered by AI agents (Nano Banana images, Kling 3.0 video, Eleven Labs Uzbek TTS).

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CLI (main.py)                        │
├──────────┬──────────┬───────────┬───────────────────────┤
│ generate │ schedule │ strategy  │ analytics             │
└────┬─────┴────┬─────┴─────┬─────┴───────────────────────┘
     │          │           │
     ▼          ▼           ▼
┌─────────────────────────────────────────────────────────┐
│              CreativeCrew (agents/crew.py)              │
│  ┌──────────┐ ┌────────────┐ ┌───────────────┐         │
│  │ Director │→│Screenwriter│→│PromptEngineer │         │
│  └──────────┘ └────────────┘ └───────┬───────┘         │
│                                      ▼                  │
│  ┌────────────────┐ ┌──────┐ ┌──────────────┐          │
│  │QualityReviewer │←│Editor│←│LightingArtist│          │
│  └───────┬────────┘ └──────┘ └──────────────┘          │
│          │ approved?                                    │
│          ▼                                              │
│  ┌─────────────────────┐                                │
│  │ ContentRequest (DTO)│                                │
│  └──────────┬──────────┘                                │
└─────────────┼───────────────────────────────────────────┘
              ▼
┌─────────────────────────────────────────────────────────┐
│          ContentPipeline (pipeline/orchestrator.py)     │
│  ┌────────────┐ ┌──────────┐ ┌───────────┐             │
│  │NanoBanana  │ │Kling 3.0 │ │ElevenLabs │             │
│  │(images)    │ │(video)   │ │(Uzbek TTS)│             │
│  └─────┬──────┘ └────┬─────┘ └─────┬─────┘             │
│        └──────┬───────┘             │                   │
│               ▼                     │                   │
│        ┌──────────┐                 │                   │
│        │ ffmpeg   │←────────────────┘                   │
│        │(merge)   │                                     │
│        └────┬─────┘                                     │
│             ▼                                           │
│       ┌───────────┐    ┌──────────────┐                 │
│       │ CDN Upload│───→│Instagram API │                 │
│       └───────────┘    └──────────────┘                 │
└─────────────────────────────────────────────────────────┘
```

## Agent system

6 specialized agents work as a creative crew:

| Agent | Role | Responsibility |
|-------|------|----------------|
| **DirectorAgent** | Режиссёр | Creative direction, pacing, transition decisions |
| **ScreenwriterAgent** | Сценарист | Scripts, captions, voiceover text (Uzbek), hooks, CTAs |
| **PromptEngineerAgent** | Промт-инженер | AI model prompts (Nano Banana, Kling), negative prompts |
| **LightingArtistAgent** | Свет/Художник | Color palettes, lighting setups, composition, mood |
| **EditorAgent** | Монтажёр | Scene cuts, transitions, text overlays, music mood |
| **QualityReviewerAgent** | Контроль | Quality scoring, cultural sensitivity, tech compliance |

### Agent pipeline flow
```
Director → Screenwriter → PromptEngineer → LightingArtist → Editor → QualityReviewer
                                                                          │
                                                                    approved? ──No──→ loop (max 3x)
                                                                          │
                                                                         Yes
                                                                          │
                                                                    ContentRequest → Pipeline → Instagram
```

## Skills system

Reusable capabilities available to agents:

| Skill | File | Capabilities |
|-------|------|-------------|
| **VisualSkills** | `skills/visual.py` | Rule of thirds, color harmony, lighting prompts, composition |
| **CopywritingSkills** | `skills/copywriting.py` | Uzbek hooks, AIDA/PAS formulas, emotional triggers, hashtags |
| **AudienceSkills** | `skills/audience.py` | Audience segments, peak hours, language strategy |
| **PlatformSkills** | `skills/platform.py` | Instagram specs, algorithm tips, safe zones, hashtag strategy |
| **AnalyticsSkills** | `skills/analytics.py` | Performance tracking, category analysis, content suggestions |

## Strategy engine

- `strategy/engine.py` — Weekly content planning, day-of-week themes, topic pools
- `strategy/calendar.py` — Persistent content calendar with visual display

### Day-of-week themes
| Day | Theme | Focus categories |
|-----|-------|-----------------|
| Monday | Motivation Monday | motivational, educational |
| Tuesday | Tips Tuesday | educational, tech |
| Wednesday | Wisdom Wednesday | educational, motivational |
| Thursday | Throwback Thursday | travel, lifestyle, fashion |
| Friday | Food Friday | recipe, lifestyle |
| Saturday | Style Saturday | fashion, lifestyle, product |
| Sunday | Story Sunday | travel, motivational, lifestyle |

## Content queue

`pipeline/queue.py` — Priority-based publication queue:
- Persistent JSON storage (survives restarts)
- Priority 1-10 (higher = published first)
- Deduplication by topic
- Auto-retry on failure (max 3 attempts, priority degrades)
- Bulk enqueue from calendar slots

## A/B testing

`pipeline/ab_testing.py` — Multi-variant content experiments:

| Strategy | What varies | Use case |
|----------|-------------|----------|
| `visual_style` | Photorealistic vs Cinematic vs Illustration | Find best visual approach |
| `hook_style` | Question vs Statement vs Number | Find best hook format |
| `pacing` | Cinematic slow vs Dynamic fast | Find best video rhythm |
| `duration` | 5s vs 10s | Find optimal video length |

Winner determined by composite score: `engagement_rate * 0.4 + reach * 0.3 + saves * 0.3`

## Content approval workflow

`pipeline/approval.py` — Review before publishing:
- Submit generated content for manual review
- Approve/reject via CLI or webhook API
- Approved content auto-enqueued with priority 9
- Quality scores displayed for reviewer decision

## Batch processing

`pipeline/batch.py` — Generate multiple content pieces:
- Process entire queue in one pass
- Configurable concurrency (sequential or parallel)
- Aggregate results with success rate

## Notifications

`notifications.py` — Multi-channel alerting:
- **Telegram** — Publish/fail alerts to Telegram bot
- **Webhook** — POST to Slack/Discord/custom URL
- **Log** — Always active as fallback
- Auto-notifies on scheduler publish/fail events

## Hashtag research

`skills/hashtags.py` — Optimal hashtag selection:
- 6 category pools (motivational, recipe, travel, lifestyle, education, fitness)
- 3-tier strategy: broad (>1M), mid (100K-1M), niche (<100K)
- Banned/shadowban hashtag detection (follow4follow, l4l, etc.)
- Optimal count: 8-15 per post

## Content template library

`templates/library.py` — 11 pre-built content blueprints:
- Categories: motivational, recipe, travel, lifestyle, education, fitness
- Each template includes: caption, hashtags, voiceover, image prompt, style preset
- Renderable with placeholder variables
- Directly enqueueable from CLI

## Data backup/restore

`utils/backup.py` — Protect JSON data files:
- Backs up 8 data files (queue, calendar, history, tests, insights, etc.)
- Timestamped snapshots with manifests
- Auto-backup before restore operations
- Retention policy (keep last 10 backups)

## Metrics

`utils/metrics.py` — Lightweight Prometheus-compatible metrics:
- Counters, gauges, histograms (thread-safe singleton)
- Context manager timer for API latency
- Prometheus text export (`/metrics` endpoint)
- Human-readable display

## Token management

`utils/token_refresh.py` — Instagram token lifecycle:
- Auto-detect expiry via Graph API probe
- Refresh 7 days before expiration
- Auto-update `.env` file with new token

## Multi-language support

`skills/localization.py` — Caption generation in 3 languages:
- **Uzbek (uz)** — Primary audience, native CTAs
- **Russian (ru)** — Bilingual Uzbek audience
- **English (en)** — International reach
- Per-language hashtag pools (4 categories each)
- Per-language CTAs (follow, like, save, comment, share)
- Translation scaffolding (extensible to API-based translation)

## Engagement optimizer

`strategy/optimizer.py` — Best posting times per platform:
- Analyzes historical performance data
- Default optimal times from industry data (7 platforms)
- Confidence levels: default → low → medium → high
- Generates optimized multi-platform schedule
- Best days of week per platform

## Brand watermarks

`utils/watermark.py` — Brand protection for images and videos:
- Text watermarks (@handle, brand name)
- Logo overlay watermarks (PNG with transparency)
- 5 position options (bottom-right, bottom-left, top-right, top-left, center)
- Opacity control (0.0-1.0)
- Per-platform skip rules
- Video watermarks via ffmpeg

## Data export/import

`utils/export_import.py` — Portable data archives:
- Exports 12 data sources to a single JSON file
- Import with replace or merge modes
- Auto-backup before import
- Archive viewer with stats

## Plugin system

`plugins/__init__.py` — Extensible hook architecture:
- 7 hook events: `on_pre_generate`, `on_post_generate`, `on_published`, `on_failed`, `on_moderation`, `on_schedule`, `on_queue_add`
- Supports sync and async handlers
- Auto-discovery from `plugins/` directory
- Example plugin included (`example_logger.py`)

## Media validation

`utils/media_validator.py` — Instagram spec compliance:
- Image: dimensions (320-4096px), format (.jpg/.png/.webp), file size (<8MB)
- Video: format (.mp4/.mov), file size (<100MB), duration limits
- Aspect ratio warnings (9:16 for stories/reels, 4:5 for feed)
- CLI: `python main.py validate ./image.png --type reel`

## Webhook authentication

`utils/auth.py` — API key protection:
- Supports `Authorization: Bearer <key>` and `X-API-Key: <key>` headers
- `/health` is always public (no auth required)
- Instagram webhook uses its own HMAC-SHA256 signature
- Disabled when `WEBHOOK_API_KEY` is not set

## System dashboard

`utils/dashboard.py` — Unified status overview:
- Queue depth, circuit breaker states, rate limiter usage
- Token health, notification channels, active plugins
- Top metrics counters, recent post history
- CLI: `python main.py dashboard`

## Pipeline metrics instrumentation

`pipeline/orchestrator.py` — Every stage is metered:
- `pipeline_runs_total` — Counter per content type
- `pipeline_published_total` / `pipeline_errors_total` / `pipeline_blocked_total`
- `api_latency_seconds` — Histogram per provider (NanoBanana, Kling, ElevenLabs, Instagram)
- `api_calls_total` — Counter per provider
- `cdn_upload_seconds`, `ffmpeg_merge_seconds`, `pipeline_moderation_seconds`

## Webhook server

`webhook.py` — HTTP API for monitoring and triggers:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check + version |
| `/status` | GET | Queue + circuit breakers + token status |
| `/queue` | GET | View content queue |
| `/calendar` | GET | View content calendar |
| `/analytics` | GET | Analytics report |
| `/trends` | GET | Current trending topics |
| `/review` | GET | Content review queue |
| `/webhook/instagram` | POST | Instagram insights callback |
| `/trigger/generate` | POST | Trigger content generation |
| `/trigger/trends` | POST | Auto-enqueue trending topics |
| `/review/approve/:id` | POST | Approve content for publishing |
| `/review/reject/:id` | POST | Reject content |
| `/metrics` | GET | Prometheus metrics export |
| `/hashtags` | GET | Hashtag pools & suggestions |
| `/library` | GET | Content template library |
| `/cms` | GET | CMS content listing |
| `/campaigns` | GET | Campaign listing |
| `/assets` | GET | Asset library |
| `/rules` | GET | Publishing rules |
| `/report` | GET | Cross-platform analytics |
| `/optimizer` | GET | Best posting times |
| `/languages` | GET | Language profiles |
| `/dashboard` | GET | Full system dashboard |
| `/cms/create` | POST | Create CMS content item |
| `/cms/crosspost/:id` | POST | Cross-post content |
| `/export` | POST | Export all data |
| `/import` | POST | Import data archive |

## Content Management System (CMS)

`cms/` — Full content lifecycle and multi-platform publishing:

### Content Manager (`cms/content_manager.py`)
Lifecycle: `draft → review → approved → scheduled → publishing → published → archived`
- CRUD operations on content items
- Status transitions with timestamps
- Platform-specific versions per item
- Campaign and tag association

### Cross-Poster (`cms/cross_poster.py`)
Adapts and publishes to 7 platforms with automatic adjustments:

| Platform | Caption Limit | Hashtags | Content Types |
|----------|:---:|:---:|---|
| Instagram | 2,200 | 30 | image, reel, carousel, story |
| Twitter/X | 280 | 5 | text, image, video, thread |
| TikTok | 2,200 | 30 | video, photo_carousel |
| YouTube | 100 (title) | 15 | short, video |
| Facebook | 63,206 | 30 | text, image, video, reel |
| Telegram | 1,024 | — | text, image, video, album |
| LinkedIn | 3,000 | 5 | text, image, article |

Auto-adaptations:
- Twitter threads for long captions (auto-split with numbering)
- YouTube #Shorts tag injection
- Telegram inline hashtags
- LinkedIn professional tone
- Content type mapping (reel→short on YouTube, carousel→album on Telegram)

### Publishing Router (`cms/publisher.py`)
Rules-based content dispatch:

| Rule | Content Match | Target Platforms |
|------|--------------|-----------------|
| Reels | type=reel | IG, TikTok, YouTube, Facebook |
| Images | type=image | IG, Facebook, Telegram, LinkedIn |
| Carousels | type=carousel | IG, Facebook, Telegram, TikTok |
| Recipes | cat=recipe | IG, Facebook, Telegram |
| Motivational | cat=motivational | All 7 platforms |

### Asset Library (`cms/asset_library.py`)
- Tag-based organization and search
- Auto-detect media type, dimensions, format, size
- Usage tracking (which content used which asset)
- Unused asset discovery

### Campaign Manager (`cms/campaigns.py`)
- Named campaigns with date ranges and goals
- Track content items per campaign
- Published/failed counts
- Pause/resume/complete lifecycle

### Analytics Aggregator (`cms/analytics_aggregator.py`)
- Unified metrics across all platforms
- Platform comparison (impressions, engagement, likes)
- Category performance breakdown
- Top performer identification

## Social Media Clients (12 total)

| Client | File | API |
|--------|------|-----|
| **NanoBanana** | `clients/nano_banana.py` | Image generation |
| **Kling** | `clients/kling.py` | Video generation (Kling 3.0) |
| **ElevenLabs** | `clients/elevenlabs.py` | Uzbek TTS |
| **Instagram** | `clients/instagram.py` | Graph API (image, reel, carousel, story) |
| **Twitter/X** | `clients/twitter.py` | v2 API (tweet, thread, media upload) |
| **TikTok** | `clients/tiktok.py` | Content Posting API (video, photo) |
| **YouTube** | `clients/youtube.py` | Data API v3 (Shorts upload) |
| **Facebook** | `clients/facebook.py` | Graph API (text, photo, video, reel) |
| **Telegram** | `clients/telegram_channel.py` | Bot API (message, photo, video, album) |
| **LinkedIn** | `clients/linkedin.py` | Marketing API (text, image, article) |
| **Pinterest** | `clients/pinterest.py` | API v5 (pin, video pin, boards) |
| **Threads** | `clients/threads.py` | Threads API (text, image, video, carousel) |

## Deployment (Docker)

```bash
# Start scheduler + webhook (production)
docker compose up -d scheduler webhook

# One-shot generation
docker compose run --rm generate auto-generate -c motivational -t "Muvaffaqiyat"

# View logs
docker compose logs -f scheduler
```

## Content moderation

`skills/moderation.py` — Pre-publish safety checks:
- Blocked content detection (scams, adult, drugs)
- Instagram engagement-bait pattern detection
- Uzbek cultural sensitivity (religion, politics, ethnicity — flagged for review)
- Positive cultural markers boost (oila, mehnat, hurmat, an'ana)
- Caption length + emoji density validation
- Pipeline auto-blocks content scoring below 70% safety

## Resilience layer

`utils/rate_limiter.py` — Token bucket per API provider:
- NanoBanana: 0.5 req/s, burst 5
- Kling: 0.17 req/s, burst 3
- ElevenLabs: 0.33 req/s, burst 4
- Instagram: 3.3 req/s, burst 10

`utils/circuit_breaker.py` — Prevents cascading failures:
- States: CLOSED → OPEN → HALF_OPEN → CLOSED
- Opens after 3-5 failures, recovers after 60-300s
- Half-open allows 2 test calls before closing

## Content recycling

`strategy/recycler.py` — Repurpose top performers:

| Strategy | Source → Target | Min age |
|----------|----------------|---------|
| `reel_to_carousel` | Reel → Carousel | 14 days |
| `reel_to_story` | Reel → Story | 7 days |
| `image_to_reel` | Image → Reel | 21 days |
| `new_angle` | Any → Same | 30 days |

Recycle score = base 5.0 + engagement boost + reach + saves

## Trending topics

`strategy/trends.py` — Seasonal & calendar-driven content:
- 13 Uzbek calendar events (Navro'z, Mustaqillik, Hayit, etc.)
- Monthly evergreen trends (12 months fully mapped)
- Trending hashtag aggregation
- Auto-enqueue trending topics to content queue

## Multi-account support

`accounts.py` — Manage multiple Instagram business accounts:
- Per-account brand voice, categories, posting schedule
- Per-account visual identity and CDN folder
- Activate/deactivate accounts

## Directory structure

```
instagram-generator/
├── CLAUDE.md              # This file
├── main.py                # CLI entry point (44 commands)
├── config.py              # Settings via .env
├── scheduler.py           # Auto-posting scheduler
├── Makefile               # Build/dev/deploy shortcuts
├── webhook.py             # HTTP webhook server (25 endpoints, API key auth)
├── accounts.py            # Multi-account management
├── notifications.py       # Telegram/webhook/log notifications
├── Dockerfile             # Container image
├── docker-compose.yml     # Production deployment
├── agents/                # Multi-agent system
│   ├── base.py            # Base classes, CreativeBrief
│   ├── crew.py            # CreativeCrew orchestrator
│   ├── director.py        # Director agent
│   ├── screenwriter.py    # Screenwriter agent
│   ├── prompt_engineer.py # Prompt engineer agent
│   ├── lighting_artist.py # Lighting/art director agent
│   ├── editor.py          # Editor agent
│   └── quality_reviewer.py# Quality control agent
├── cms/                   # Content management system
│   ├── content_manager.py # Full content lifecycle
│   ├── cross_poster.py    # Multi-platform publishing + adaptation
│   ├── publisher.py       # Rules-based routing engine
│   ├── asset_library.py   # Media asset library with tagging
│   ├── campaigns.py       # Campaign management
│   ├── analytics_aggregator.py  # Cross-platform analytics
│   └── versioning.py      # Content version history
├── clients/               # Social media & API clients (12)
│   ├── nano_banana.py     # Image generation
│   ├── kling.py           # Video generation (Kling 3.0)
│   ├── elevenlabs.py      # Uzbek TTS
│   ├── instagram.py       # Instagram Graph API
│   ├── twitter.py         # Twitter/X v2 API
│   ├── tiktok.py          # TikTok Content Posting API
│   ├── youtube.py         # YouTube Data API (Shorts)
│   ├── facebook.py        # Facebook Pages Graph API
│   ├── telegram_channel.py# Telegram Bot API (channels)
│   ├── linkedin.py        # LinkedIn Marketing API
│   ├── pinterest.py       # Pinterest API v5
│   └── threads.py         # Threads API (Meta)
├── pipeline/              # Content generation pipeline
│   ├── orchestrator.py    # End-to-end pipeline (with moderation + resilience)
│   ├── queue.py           # Priority content queue
│   ├── ab_testing.py      # A/B testing engine
│   ├── approval.py        # Content review workflow
│   └── batch.py           # Batch processing engine
├── skills/                # Reusable creative skills
│   ├── visual.py          # Visual composition
│   ├── copywriting.py     # Uzbek copywriting
│   ├── audience.py        # Audience targeting
│   ├── platform.py        # Instagram optimization
│   ├── analytics.py       # Performance analytics
│   ├── moderation.py      # Content safety & cultural checks
│   ├── hashtags.py        # Hashtag research & banned detection
│   ├── localization.py    # Multi-language captions (uz, ru, en)
│   └── deduplication.py   # Content duplicate detection
├── strategy/              # Content strategy
│   ├── engine.py          # Strategy planner
│   ├── calendar.py        # Content calendar
│   ├── recycler.py        # Content recycling engine
│   ├── trends.py          # Trending topics & seasonal events
│   ├── optimizer.py       # Best-time-to-post per platform
│   └── competitors.py    # Competitor account tracking
├── plugins/               # Extension system
│   ├── __init__.py        # Plugin registry + hook system
│   └── example_logger.py  # Example plugin (logging hooks)
├── templates/             # Content templates
│   ├── prompts.py         # Prompt templates
│   └── library.py         # Pre-built content blueprints (11 templates)
├── tests/                 # Test suite (pytest)
│   ├── conftest.py        # Fixtures + mocked clients
│   ├── test_agents.py     # Agent system tests
│   ├── test_circuit_breaker.py
│   ├── test_moderation.py # Moderation tests
│   ├── test_queue.py      # Queue tests
│   ├── test_rate_limiter.py
│   ├── test_strategy.py   # Strategy engine tests
│   ├── test_trends.py     # Trends engine tests
│   ├── test_pipeline.py   # Integration tests (mocked)
│   ├── test_approval.py   # Approval workflow tests
│   ├── test_notifications.py  # Notification tests
│   ├── test_hashtags.py   # Hashtag research tests
│   ├── test_backup.py     # Backup/restore tests
│   ├── test_metrics.py    # Metrics collection tests
│   ├── test_templates.py  # Template library tests
│   ├── test_plugins.py    # Plugin system tests
│   ├── test_media_validator.py  # Media validation tests
│   ├── test_auth.py       # Webhook auth tests
│   ├── test_cms.py        # CMS + cross-poster + router + campaign tests
│   ├── test_localization.py  # Multi-language tests
│   ├── test_optimizer.py  # Engagement optimizer tests
│   ├── test_export.py     # Export/import tests
│   ├── test_dedup_competitors.py  # Dedup + competitor tests
│   └── test_versioning.py # Content version tests
└── utils/                 # Utilities
    ├── cdn.py             # S3/R2/MinIO/HTTP upload
    ├── media.py           # ffmpeg operations
    ├── rate_limiter.py    # Token bucket rate limiting
    ├── circuit_breaker.py # Circuit breaker pattern
    ├── startup.py         # Environment validation
    ├── logging.py         # Structured logging (dev/prod)
    ├── token_refresh.py   # Instagram token auto-refresh
    ├── backup.py          # Data backup/restore
    ├── metrics.py         # Prometheus-compatible metrics
    ├── auth.py            # Webhook API key authentication
    ├── media_validator.py # Image/video quality validation
    ├── dashboard.py       # Live system dashboard
    ├── watermark.py       # Brand watermark (image + video)
    ├── export_import.py   # Data export/import (portable JSON)
    ├── health.py          # API provider health monitoring
    └── ical.py            # iCal calendar feed export
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest -v                                    # All tests
pytest --cov=. --cov-report=term-missing     # Coverage
pytest -m "not integration"                  # Skip API tests
```

## CI/CD

`.github/workflows/ci.yml` — lint (ruff) → typecheck (mypy) → test (pytest, 40% min coverage) → docker build

## Startup diagnostics

```bash
python main.py doctor          # Check env, ffmpeg, API keys
python main.py doctor --strict # Require all API keys
```

## Content versioning

`cms/versioning.py` — Track edit history:
- Every update creates a numbered version snapshot
- Compare any two versions (field-level diff)
- Rollback capability

## Duplicate detection

`skills/deduplication.py` — Prevent similar content:
- Exact topic+category match detection
- Fuzzy title similarity (token overlap ratio, threshold 65%)
- Caption n-gram similarity
- 30-day lookback window

## Competitor tracking

`strategy/competitors.py` — Monitor competitor accounts:
- Track followers, avg likes/comments, posting frequency
- Historical snapshots for growth analysis
- Cross-competitor hashtag and category analysis

## API health monitoring

`utils/health.py` — Check all provider uptime:
- Ping 12 API endpoints (generation + publishing)
- Status: up/down/degraded + latency
- Critical-only mode (NanoBanana, Kling, ElevenLabs, Instagram)

## iCal calendar feed

`utils/ical.py` — Export schedule as .ics:
- CMS scheduled items and content calendar as VEVENT
- Standard iCal format (Google Calendar, Outlook compatible)
- Configurable source (cms, calendar, all)

## CLI commands (44 total)

```bash
# === Content Generation ===
python main.py auto-generate -c motivational -t "Muvaffaqiyat"   # Agent-driven
python main.py generate --template morning_motivation             # Template-based

# === Strategy & Planning ===
python main.py strategy --plan-week                               # Plan weekly calendar
python main.py strategy --plan-day                                # Plan today
python main.py trends                                             # Show trending topics
python main.py trends --plan                                      # Auto-enqueue trends
python main.py trends --hashtags                                  # Trending hashtags
python main.py recycle                                            # Find recyclable content
python main.py recycle -s new_angle --generate                    # Generate recycled content

# === Queue Management ===
python main.py queue                                              # View queue
python main.py queue --add -t "Palov" -c recipe                   # Add to queue
python main.py queue --from-calendar                              # Bulk enqueue from calendar
python main.py queue --process                                    # Process next item

# === A/B Testing ===
python main.py ab-test -t "Muvaffaqiyat" -c motivational -s visual_style
python main.py ab-test -t "Palov" -c recipe -s duration --dry-run

# === Safety & Moderation ===
python main.py moderate -t "Your caption text" -h "tag1,tag2"     # Check content safety
python main.py status                                             # Circuit breakers + rate limits

# === Automation ===
python main.py schedule                                           # Start auto-poster
python main.py schedule --times 10:00,14:00,19:00                 # Custom times
python main.py webhook --port 8080                                # Start webhook server

# === Account Management ===
python main.py accounts                                           # List accounts
python main.py accounts --add --id brand1 --name "My Brand"       # Add account

# === Monitoring ===
python main.py analytics --report                                 # Performance report
python main.py analytics --suggest                                # AI suggestions
python main.py history                                            # Post history
python main.py templates                                          # List templates
python main.py doctor                                             # Startup diagnostics
python main.py doctor --strict                                    # Require all keys

# === Batch Processing ===
python main.py batch --from-queue -l 10                           # Process 10 queue items
python main.py batch --from-queue -l 5 -c 2                       # 5 items, 2 parallel

# === Content Review ===
python main.py review                                             # View review queue
python main.py review --pending                                   # Pending items only
python main.py review --approve abc123 -n "Looks great"           # Approve item
python main.py review --reject abc123 -n "Caption too short"      # Reject item

# === Token Management ===
python main.py token                                              # Token status
python main.py token --check                                      # Verify + auto-refresh
python main.py token --refresh                                    # Force refresh

# === Notifications ===
python main.py notify --test                                      # Send test notification
python main.py notify -m "Custom message"                         # Send custom message

# === Hashtag Research ===
python main.py hashtags -c recipe                                 # Suggest hashtags
python main.py hashtags -c motivational -n 15                     # 15 hashtags
python main.py hashtags --check "follow4follow,success"           # Check for bans

# === Data Backup ===
python main.py backup --create -l "before_deploy"                 # Create backup
python main.py backup --restore 20260323_120000_before_deploy     # Restore
python main.py backup                                             # List backups

# === Metrics ===
python main.py metrics                                            # Human-readable
python main.py metrics --prometheus                               # Prometheus format
python main.py metrics --json                                     # JSON export

# === Template Library ===
python main.py library                                            # Browse all templates
python main.py library -c recipe                                  # Filter by category
python main.py library --use palov_recipe                         # Use + enqueue

# === System Dashboard ===
python main.py dashboard                                          # Full system overview

# === Plugins ===
python main.py plugins                                            # View loaded plugins
python main.py plugins --load                                     # Discover + load plugins

# === Media Validation ===
python main.py validate ./output/image.png --type image           # Validate image
python main.py validate ./output/video.mp4 --type reel            # Validate video

# === Content CMS ===
python main.py content --create -t "Palov" -c recipe              # Create draft
python main.py content --list                                     # List all content
python main.py content --status draft                             # Filter by status
python main.py content --search "palov"                           # Search content
python main.py content --submit abc123                            # Submit for review
python main.py content --approve abc123                           # Approve
python main.py content --schedule-id abc123 --platforms "instagram,tiktok"
python main.py content --archive abc123                           # Archive

# === Cross-Posting ===
python main.py crosspost --content-id abc123                      # Auto-route + publish
python main.py crosspost --content-id abc123 -p "instagram,tiktok" # Specific platforms
python main.py crosspost --rules                                  # View publishing rules
python main.py crosspost --route --content-id abc123              # Preview routing

# === Campaigns ===
python main.py campaign --create --name "Navro'z 2026" --platforms "instagram,tiktok"
python main.py campaign --list                                    # List campaigns
python main.py campaign --complete abc123                         # Complete campaign
python main.py campaign --pause abc123                            # Pause campaign

# === Media Assets ===
python main.py assets                                             # View asset library
python main.py assets --add ./output/image.png --tags "recipe,palov"
python main.py assets --search "palov"                            # Search assets
python main.py assets --unused                                    # Find unused assets

# === Cross-Platform Analytics ===
python main.py report                                             # Full cross-platform report
python main.py report --platforms                                 # Platform breakdown
python main.py report --categories                                # Category breakdown
python main.py report --top 5                                     # Top 5 performers

# === Engagement Optimizer ===
python main.py optimizer                                          # All platforms
python main.py optimizer -p instagram                             # Single platform
python main.py optimizer --schedule                               # Generate optimal schedule
python main.py optimizer --schedule --posts-per-day 4             # Custom frequency

# === Multi-Language ===
python main.py localize -t "Palov tayyorlash!" -c recipe          # Localize caption
python main.py localize --info                                    # Language profiles

# === Data Export/Import ===
python main.py export -o ./backup.json                            # Export all data
python main.py import ./backup.json                               # Import (replace)
python main.py import ./backup.json --merge                       # Import (merge)

# === Duplicate Detection ===
python main.py dedup -t "Palov recipe"                            # Check for duplicates
python main.py dedup -s "Morning motivation"                      # Find similar content

# === Competitor Tracking ===
python main.py competitors                                        # View all competitors
python main.py competitors --add --name "Rival" -p instagram --handle "@rival"
python main.py competitors --update abc123 --followers 50000 --avg-likes 2000

# === Content Versions ===
python main.py versions                                           # Version summary
python main.py versions --content-id abc123                       # Item version history
python main.py versions --content-id abc123 --diff 1:2            # Compare versions

# === API Health ===
python main.py health --check                                     # Check all 12 providers
python main.py health --critical                                  # Check 4 critical APIs

# === iCal Export ===
python main.py ical                                               # Export schedule.ics
python main.py ical -o ./calendar.ics --source cms                # CMS items only
```

## Makefile

```bash
make help       # Show all commands
make install    # Production deps
make dev        # Dev deps (pytest, ruff, mypy)
make check      # Lint + typecheck + test
make test       # Run tests
make test-cov   # Tests with coverage
make docker     # Build image
make docker-up  # Start production stack
make clean      # Remove cache files
```

## Configuration

All settings via environment variables (`.env` file):

**API keys:**
- `NANO_BANANA_API_KEY` — Image generation
- `KLING_API_KEY` — Video generation (Kling 3.0)
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` — Uzbek TTS
- `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_BUSINESS_ACCOUNT_ID` — Instagram Graph API

**CDN (S3-compatible):**
- `CDN_PROVIDER` — `s3`, `r2`, `minio`, or `http`
- `CDN_BUCKET_NAME`, `CDN_REGION`, `CDN_ENDPOINT_URL`, `CDN_PUBLIC_URL`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

**Queue & A/B:**
- `QUEUE_ENABLED`, `QUEUE_MAX_SIZE`
- `AB_TESTING_ENABLED`, `AB_VARIANT_COUNT`

**General:**
- `TIMEZONE` — Default: `Asia/Tashkent`
- `WEBHOOK_PORT`, `WEBHOOK_SECRET`

## Content types supported
- **Reel** — Image → Video → Voiceover → Merge → Subtitles → Publish
- **Image** — Single image post with caption
- **Carousel** — Multi-slide educational/fashion content
- **Story** — Ephemeral visual content

## Language
Primary: **Uzbek (uz)** — all voiceovers, captions, hooks, CTAs
Secondary: English hashtags for discoverability

## Quality gates
- Average quality score must be ≥ 7.0/10
- Cultural sensitivity must be ≥ 8.0/10
- Brand alignment must be ≥ 6.0/10
- Maximum 3 revision rounds before force-publish
