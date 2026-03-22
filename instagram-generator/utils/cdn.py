"""CDN upload — S3, Cloudflare R2, MinIO, or HTTP upload.

Provider selection via CDN_PROVIDER env var:
  - "s3"   → AWS S3 (default)
  - "r2"   → Cloudflare R2
  - "minio" → MinIO
  - "http"  → Generic HTTP upload endpoint
"""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)


def _generate_key(file_path: Path) -> str:
    """Generate a unique CDN key for a file."""
    content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()[:10]
    return f"instagram/{content_hash}_{file_path.stem}{file_path.suffix}"


async def upload_to_cdn(file_path: Path) -> str:
    """Upload a file to CDN and return its public URL.

    Dispatches to the configured provider (s3/r2/minio/http).
    """
    provider = settings.cdn_provider.lower()

    if provider in ("s3", "r2", "minio"):
        return await _upload_s3_compatible(file_path)
    elif provider == "http":
        return await _upload_http(file_path)
    else:
        raise ValueError(f"Unknown CDN provider: {provider}")


# ------------------------------------------------------------------
# S3-compatible upload (AWS S3, Cloudflare R2, MinIO)
# ------------------------------------------------------------------

async def _upload_s3_compatible(file_path: Path) -> str:
    """Upload via boto3 to S3/R2/MinIO."""
    try:
        import boto3
        from botocore.config import Config as BotoConfig
    except ImportError:
        raise RuntimeError(
            "boto3 is required for S3 uploads. Install it:\n"
            "  pip install boto3"
        )

    key = _generate_key(file_path)
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    # Build S3 client config
    client_kwargs = {
        "service_name": "s3",
        "region_name": settings.cdn_region,
    }

    # Use explicit credentials if provided
    if settings.aws_access_key_id:
        client_kwargs["aws_access_key_id"] = settings.aws_access_key_id
        client_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key

    # Custom endpoint for R2/MinIO
    if settings.cdn_endpoint_url:
        client_kwargs["endpoint_url"] = settings.cdn_endpoint_url

    s3 = boto3.client(**client_kwargs)

    logger.info(
        "cdn.s3.uploading",
        bucket=settings.cdn_bucket_name,
        key=key,
        size_kb=file_path.stat().st_size // 1024,
    )

    s3.upload_file(
        str(file_path),
        settings.cdn_bucket_name,
        key,
        ExtraArgs={
            "ContentType": mime_type,
            "ACL": "public-read",
        },
    )

    # Build public URL
    if settings.cdn_public_url:
        public_url = f"{settings.cdn_public_url.rstrip('/')}/{key}"
    elif settings.cdn_endpoint_url:
        public_url = f"{settings.cdn_endpoint_url.rstrip('/')}/{settings.cdn_bucket_name}/{key}"
    else:
        public_url = f"https://{settings.cdn_bucket_name}.s3.{settings.cdn_region}.amazonaws.com/{key}"

    logger.info("cdn.s3.uploaded", url=public_url)
    return public_url


# ------------------------------------------------------------------
# HTTP upload (generic endpoint)
# ------------------------------------------------------------------

async def _upload_http(file_path: Path) -> str:
    """Upload via HTTP POST to a generic upload endpoint."""
    if not settings.cdn_upload_url:
        raise ValueError(
            "CDN_UPLOAD_URL must be set for HTTP provider. "
            "Or switch to CDN_PROVIDER=s3 and configure S3 credentials."
        )

    key = _generate_key(file_path)
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    headers = {}
    if settings.cdn_api_key:
        headers["Authorization"] = f"Bearer {settings.cdn_api_key}"

    logger.info("cdn.http.uploading", endpoint=settings.cdn_upload_url)

    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(file_path, "rb") as f:
            resp = await client.post(
                settings.cdn_upload_url,
                files={"file": (key.split("/")[-1], f, mime_type)},
                headers=headers,
            )
        resp.raise_for_status()

    public_url = f"{settings.cdn_public_url.rstrip('/')}/{key}"
    logger.info("cdn.http.uploaded", url=public_url)
    return public_url
