"""Centralized configuration via environment variables.

All API keys and settings loaded from .env file.
Supports: PiAPI, Claude, NanoBanana, Kling, ElevenLabs,
Instagram, Twitter, TikTok, YouTube, Facebook, Telegram,
LinkedIn, Pinterest, Threads, CDN, Queue, Webhook.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- AI Content Generation ---
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6-20250514"

    # --- PiAPI (Unified AI Gateway — PRIMARY) ---
    piapi_api_key: str = ""

    # --- Nano Banana (Legacy fallback) ---
    nano_banana_api_key: str = ""
    nano_banana_base_url: str = "https://api.nanobanana.com/v1"

    # --- Kling (Legacy fallback) ---
    kling_api_key: str = ""
    kling_base_url: str = "https://api.klingai.com/v1"

    # --- Eleven Labs (Uzbek TTS) ---
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # --- Instagram ---
    instagram_access_token: str = ""
    instagram_business_account_id: str = ""

    # --- Twitter/X ---
    twitter_bearer_token: str = ""
    twitter_api_key: str = ""
    twitter_api_secret: str = ""
    twitter_access_token: str = ""
    twitter_access_secret: str = ""

    # --- TikTok ---
    tiktok_access_token: str = ""

    # --- YouTube ---
    youtube_access_token: str = ""
    youtube_api_key: str = ""

    # --- Facebook ---
    facebook_page_access_token: str = ""
    facebook_page_id: str = ""

    # --- Telegram Channel ---
    telegram_channel_bot_token: str = ""
    telegram_channel_id: str = ""

    # --- LinkedIn ---
    linkedin_access_token: str = ""
    linkedin_organization_id: str = ""
    linkedin_person_id: str = ""

    # --- Pinterest ---
    pinterest_access_token: str = ""
    pinterest_board_id: str = ""

    # --- Threads ---
    threads_access_token: str = ""
    threads_user_id: str = ""

    # --- Notifications ---
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    notify_webhook_url: str = ""

    # --- CDN / S3-compatible storage ---
    cdn_provider: str = "s3"
    cdn_bucket_name: str = ""
    cdn_region: str = "us-east-1"
    cdn_endpoint_url: str = ""
    cdn_public_url: str = ""
    cdn_upload_url: str = ""
    cdn_api_key: str = ""
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # --- Content queue ---
    queue_enabled: bool = True
    queue_max_size: int = 50
    queue_file: str = "content_queue.json"

    # --- A/B testing ---
    ab_testing_enabled: bool = False
    ab_variant_count: int = 2

    # --- Webhook ---
    webhook_port: int = 8080
    webhook_secret: str = ""
    webhook_api_key: str = ""

    # --- General ---
    content_output_dir: Path = Path("./output")
    log_level: str = "INFO"
    log_format: str = ""
    post_schedule_cron: str = "0 9,13,18 * * *"
    timezone: str = "Asia/Tashkent"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
