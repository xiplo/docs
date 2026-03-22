# Instagram Content Generator — CLAUDE.md

## Project overview

Automated Instagram content generation and auto-posting system for Uzbek-language audience.
Integrates Nano Banana (images), Kling 3.0 (video), Eleven Labs (Uzbek TTS), and Instagram Graph API.

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

## Token management

`utils/token_refresh.py` — Instagram token lifecycle:
- Auto-detect expiry via Graph API probe
- Refresh 7 days before expiration
- Auto-update `.env` file with new token

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
├── main.py                # CLI entry point (22 commands)
├── config.py              # Settings via .env
├── scheduler.py           # Auto-posting scheduler
├── webhook.py             # HTTP webhook server (12 endpoints)
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
├── clients/               # External API clients
│   ├── nano_banana.py     # Image generation
│   ├── kling.py           # Video generation (Kling 3.0)
│   ├── elevenlabs.py      # Uzbek TTS
│   └── instagram.py       # Instagram Graph API
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
│   └── moderation.py      # Content safety & cultural checks
├── strategy/              # Content strategy
│   ├── engine.py          # Strategy planner
│   ├── calendar.py        # Content calendar
│   ├── recycler.py        # Content recycling engine
│   └── trends.py          # Trending topics & seasonal events
├── templates/             # Content templates
│   └── prompts.py         # Template library
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
│   └── test_notifications.py  # Notification tests
└── utils/                 # Utilities
    ├── cdn.py             # S3/R2/MinIO/HTTP upload
    ├── media.py           # ffmpeg operations
    ├── rate_limiter.py    # Token bucket rate limiting
    ├── circuit_breaker.py # Circuit breaker pattern
    ├── startup.py         # Environment validation
    ├── logging.py         # Structured logging (dev/prod)
    └── token_refresh.py   # Instagram token auto-refresh
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

## CLI commands (22 total)

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
