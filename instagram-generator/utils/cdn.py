"""CDN upload implementation using S3-compatible storage.

Supports:
  - AWS S3
  - Cloudflare R2
  - MinIO
  - Any S3-compatible service

Set these env vars:
  CDN_BUCKET_NAME=your-bucket
  CDN_REGION=us-east-1
  CDN_ENDPOINT_URL=https://your-endpoint  (for R2/MinIO)
  CDN_PUBLIC_URL=https://cdn.yourdomain.com
  AWS_ACCESS_KEY_ID=...
  AWS_SECRET_ACCESS_KEY=...
"""

from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

import httpx
import structlog

logger = structlog.get_logger(__name__)


async def upload_to_cdn(file_path: Path) -> str:
    """Upload a file and return its public URL.

    This is a simple HTTP-based upload implementation.
    For production, use boto3 with S3 presigned URLs or
    direct S3 upload.

    To use this, set up a simple upload endpoint or replace
    with your CDN provider's SDK.
    """
    import os

    cdn_upload_url = os.getenv("CDN_UPLOAD_URL")
    cdn_public_url = os.getenv("CDN_PUBLIC_URL", "")
    cdn_api_key = os.getenv("CDN_API_KEY", "")

    if not cdn_upload_url:
        raise NotImplementedError(
            "Set CDN_UPLOAD_URL env var to your upload endpoint. "
            "Or implement S3 upload using boto3:\n"
            "  pip install boto3\n"
            "  s3.upload_file(str(file_path), bucket, key)\n"
            "  return f'{cdn_public_url}/{key}'"
        )

    # Generate unique filename
    content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()[:10]
    ext = file_path.suffix
    remote_name = f"{content_hash}_{file_path.stem}{ext}"
    mime_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(file_path, "rb") as f:
            resp = await client.post(
                cdn_upload_url,
                files={"file": (remote_name, f, mime_type)},
                headers={"Authorization": f"Bearer {cdn_api_key}"} if cdn_api_key else {},
            )
        resp.raise_for_status()

    public_url = f"{cdn_public_url.rstrip('/')}/{remote_name}"
    logger.info("cdn.uploaded", path=str(file_path), url=public_url)
    return public_url
