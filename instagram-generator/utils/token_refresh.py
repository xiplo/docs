"""Instagram token auto-refresh.

Instagram long-lived tokens expire after ~60 days. This module:
  1. Tracks token expiry
  2. Auto-refreshes before expiration
  3. Saves new token to .env file

Requires:
  INSTAGRAM_APP_ID and INSTAGRAM_APP_SECRET for token exchange.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import structlog

from config import settings

logger = structlog.get_logger(__name__)

TOKEN_STATE_FILE = Path(settings.content_output_dir) / "token_state.json"
GRAPH_API_BASE = "https://graph.instagram.com"


class TokenRefresher:
    """Manages Instagram access token lifecycle."""

    REFRESH_THRESHOLD_DAYS = 7  # Refresh when less than 7 days remain

    def __init__(self) -> None:
        self._state = self._load_state()

    @property
    def current_token(self) -> str:
        return settings.instagram_access_token

    @property
    def expires_at(self) -> datetime | None:
        exp = self._state.get("expires_at")
        if exp:
            return datetime.fromisoformat(exp)
        return None

    @property
    def needs_refresh(self) -> bool:
        if not self.expires_at:
            return False
        remaining = self.expires_at - datetime.now()
        return remaining < timedelta(days=self.REFRESH_THRESHOLD_DAYS)

    @property
    def days_remaining(self) -> int | None:
        if not self.expires_at:
            return None
        return max(0, (self.expires_at - datetime.now()).days)

    async def check_and_refresh(self) -> str:
        """Check token validity and refresh if needed. Returns current token."""
        if not self.current_token:
            logger.warning("token.not_configured")
            return ""

        # Check if we know the expiry
        if not self.expires_at:
            await self._probe_token()

        if self.needs_refresh:
            logger.info(
                "token.refreshing",
                days_remaining=self.days_remaining,
            )
            return await self.refresh()

        logger.info("token.valid", days_remaining=self.days_remaining)
        return self.current_token

    async def refresh(self) -> str:
        """Exchange current token for a new long-lived token."""
        url = f"{GRAPH_API_BASE}/refresh_access_token"
        params = {
            "grant_type": "ig_refresh_token",
            "access_token": self.current_token,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        new_token = data["access_token"]
        expires_in = data.get("expires_in", 5184000)  # Default 60 days

        # Save new token state
        self._state = {
            "token": new_token,
            "refreshed_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
            "expires_in_days": expires_in // 86400,
        }
        self._save_state()

        # Update .env file
        self._update_env_file(new_token)

        logger.info(
            "token.refreshed",
            expires_in_days=expires_in // 86400,
        )

        return new_token

    async def _probe_token(self) -> None:
        """Check current token validity by making a test API call."""
        url = f"{GRAPH_API_BASE}/me"
        params = {
            "fields": "id,username",
            "access_token": self.current_token,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    # Token works, assume 60 days from now if unknown
                    if not self._state.get("expires_at"):
                        self._state["expires_at"] = (
                            datetime.now() + timedelta(days=55)
                        ).isoformat()
                        self._save_state()
                    logger.info("token.probe_ok")
                else:
                    logger.warning("token.probe_failed", status=resp.status_code)
        except Exception as exc:
            logger.warning("token.probe_error", error=str(exc))

    def get_status(self) -> dict:
        """Return token status for display."""
        return {
            "configured": bool(self.current_token),
            "expires_at": self.expires_at.isoformat() if self.expires_at else "unknown",
            "days_remaining": self.days_remaining,
            "needs_refresh": self.needs_refresh,
        }

    def _update_env_file(self, new_token: str) -> None:
        """Update the .env file with the new token."""
        env_path = Path(".env")
        if not env_path.exists():
            return

        lines = env_path.read_text().splitlines()
        updated = False
        for i, line in enumerate(lines):
            if line.startswith("INSTAGRAM_ACCESS_TOKEN="):
                lines[i] = f"INSTAGRAM_ACCESS_TOKEN={new_token}"
                updated = True
                break

        if updated:
            env_path.write_text("\n".join(lines) + "\n")
            logger.info("token.env_updated")

    def _load_state(self) -> dict:
        if TOKEN_STATE_FILE.exists():
            try:
                return json.loads(TOKEN_STATE_FILE.read_text())
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_state(self) -> None:
        TOKEN_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_STATE_FILE.write_text(json.dumps(self._state, indent=2))
