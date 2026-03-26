# Social Content CMS

Full-stack content management system for multi-platform social media. Auto-generates and cross-posts Uzbek-language content across 9 platforms.

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env — add your PIAPI_API_KEY, ANTHROPIC_API_KEY, and platform tokens

# 3. Generate content
python main.py auto-generate -c motivational -t "Muvaffaqiyat"

# 4. Start scheduler (24/7 auto-posting)
python main.py schedule
```

## Architecture

```
CLI (46 cmds) / Webhook API (25 endpoints) / Docker
    |
Content CMS (draft -> review -> approved -> scheduled -> published -> archived)
    |                    |                              |
Campaign Manager    Asset Library               Publishing Router
    |                                                  |
    |                                           Cross-Poster (9 platforms)
    |                    IG | Twitter | TikTok | YouTube | Facebook
    |                    Telegram | LinkedIn | Pinterest | Threads
    |
Queue <- CMS Scheduled <- Trends <- Templates (11)
    |
Scheduler (CMS -> queue -> trends -> strategy)
    |
CreativeCrew (6 AI agents, Claude claude-sonnet-4-6)
    |
Moderation + Media Validation + Watermark
    |
Pipeline: PiAPI (Flux images + Kling 3.0 video) -> ElevenLabs TTS -> ffmpeg -> CDN -> Publish
```

## AI Stack

| Component | Model | Purpose |
|-----------|-------|---------|
| Images | Flux (via PiAPI) | Text-to-image generation |
| Video | Kling 3.0 (via PiAPI) | Image-to-video animation |
| Video (alt) | Seedance 2.0, Veo3 (via PiAPI) | Cinematic video |
| Captions | Claude claude-sonnet-4-6 | AI-written hooks, CTAs, scripts |
| Quality | Claude claude-sonnet-4-6 | Content review + improvement |
| Voice | ElevenLabs | Uzbek TTS voiceover |

## 9 Social Platforms

Instagram, Twitter/X, TikTok, YouTube Shorts, Facebook, Telegram, LinkedIn, Pinterest, Threads

## Key Features

- **46 CLI commands** for every operation
- **25 webhook endpoints** for API access
- **6 AI agents** (Director, Screenwriter, PromptEngineer, LightingArtist, Editor, QualityReviewer)
- **CMS** with full content lifecycle
- **CRM** with audience segments, engagement tracking, follower funnel
- **Cross-posting** with platform-specific adaptation
- **A/B testing** for content optimization
- **Moderation** with Uzbek cultural sensitivity
- **Metrics** (Prometheus-compatible)
- **224 tests passing**

## Configuration

Copy `.env.example` to `.env` and set:

```bash
# Required for AI generation
PIAPI_API_KEY=your_piapi_key          # piapi.ai — images + video
ANTHROPIC_API_KEY=your_anthropic_key  # Claude claude-sonnet-4-6 — captions + review

# Required for publishing
INSTAGRAM_ACCESS_TOKEN=your_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_id

# Optional: additional platforms
TWITTER_BEARER_TOKEN=...
TIKTOK_ACCESS_TOKEN=...
# ... see .env.example for all options
```

## Docker

```bash
docker compose up -d scheduler webhook   # Production
docker compose run --rm generate auto-generate -c recipe -t "Palov"
```

## Testing

```bash
pip install -r requirements-dev.txt
pytest -v                    # 224 tests
make check                   # lint + typecheck + test
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for comprehensive system documentation.

## License

MIT
