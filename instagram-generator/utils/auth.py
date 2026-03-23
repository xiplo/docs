"""Webhook authentication middleware — API key protection for endpoints.

Protects non-Instagram endpoints with bearer token or X-API-Key header.
Instagram webhook uses its own HMAC-SHA256 signature verification.
"""

from __future__ import annotations

import os

import structlog

logger = structlog.get_logger(__name__)

# API key for webhook endpoints (set via WEBHOOK_API_KEY env var)
WEBHOOK_API_KEY = os.getenv("WEBHOOK_API_KEY", "")


def check_api_key(headers) -> bool:
    """Validate API key from request headers.

    Accepts:
      - Authorization: Bearer <key>
      - X-API-Key: <key>

    Returns True if:
      - WEBHOOK_API_KEY is not set (auth disabled)
      - Key matches
    """
    if not WEBHOOK_API_KEY:
        return True  # Auth disabled

    # Check Authorization: Bearer <key>
    auth = headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
        if token == WEBHOOK_API_KEY:
            return True

    # Check X-API-Key header
    api_key = headers.get("X-API-Key", "")
    if api_key == WEBHOOK_API_KEY:
        return True

    logger.warning("webhook.auth_failed")
    return False


# Endpoints that don't require auth
PUBLIC_ENDPOINTS = frozenset({"/health"})
