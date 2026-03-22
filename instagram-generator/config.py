"""Centralized configuration via environment variables."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Nano Banana
    nano_banana_api_key: str = ""
    nano_banana_base_url: str = "https://api.nanobanana.com/v1"

    # Kling 3.0
    kling_api_key: str = ""
    kling_base_url: str = "https://api.klingai.com/v1"

    # Eleven Labs
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""

    # Instagram
    instagram_access_token: str = ""
    instagram_business_account_id: str = ""

    # General
    content_output_dir: Path = Path("./output")
    log_level: str = "INFO"
    post_schedule_cron: str = "0 9,13,18 * * *"
    timezone: str = "Asia/Tashkent"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
