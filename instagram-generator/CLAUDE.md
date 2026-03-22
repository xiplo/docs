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

## Directory structure

```
instagram-generator/
├── CLAUDE.md              # This file
├── main.py                # CLI entry point
├── config.py              # Settings via .env
├── scheduler.py           # Auto-posting scheduler
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
│   └── orchestrator.py    # End-to-end pipeline
├── skills/                # Reusable creative skills
│   ├── visual.py          # Visual composition
│   ├── copywriting.py     # Uzbek copywriting
│   ├── audience.py        # Audience targeting
│   ├── platform.py        # Instagram optimization
│   └── analytics.py       # Performance analytics
├── strategy/              # Content strategy
│   ├── engine.py          # Strategy planner
│   └── calendar.py        # Content calendar
├── templates/             # Content templates
│   └── prompts.py         # Template library
└── utils/                 # Utilities
    ├── cdn.py             # CDN upload
    └── media.py           # ffmpeg operations
```

## Key commands

```bash
# Generate content with agent system
python main.py auto-generate --category motivational --topic "Muvaffaqiyat sirlari"

# Generate from template (legacy)
python main.py generate --template morning_motivation

# Plan and display weekly calendar
python main.py strategy --plan-week

# Start auto-posting scheduler
python main.py schedule

# View analytics
python main.py analytics

# List templates
python main.py templates
```

## Configuration

All settings via environment variables (`.env` file):
- `NANO_BANANA_API_KEY` — Image generation API
- `KLING_API_KEY` — Video generation API
- `ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID` — Uzbek TTS
- `INSTAGRAM_ACCESS_TOKEN` + `INSTAGRAM_BUSINESS_ACCOUNT_ID` — Instagram
- `CDN_UPLOAD_URL` + `CDN_PUBLIC_URL` — Media hosting
- `TIMEZONE` — Default: `Asia/Tashkent`

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
