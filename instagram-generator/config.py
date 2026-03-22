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

    # CDN / S3-compatible storage
    cdn_provider: str = "s3"  # s3, r2, minio, http
    cdn_bucket_name: str = ""
    cdn_region: str = "us-east-1"
    cdn_endpoint_url: str = ""  # Custom endpoint for R2/MinIO
    cdn_public_url: str = ""  # Public base URL for assets
    cdn_upload_url: str = ""  # HTTP upload endpoint (for http provider)
    cdn_api_key: str = ""  # API key for HTTP upload
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""

    # Content queue
    queue_enabled: bool = True
    queue_max_size: int = 50
    queue_file: str = "content_queue.json"

    # A/B testing
    ab_testing_enabled: bool = False
    ab_variant_count: int = 2

    # Webhook
    webhook_port: int = 8080
    webhook_secret: str = ""

    # General
    content_output_dir: Path = Path("./output")
    log_level: str = "INFO"
    post_schedule_cron: str = "0 9,13,18 * * *"
    timezone: str = "Asia/Tashkent"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
