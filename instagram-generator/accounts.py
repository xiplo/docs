"""Multi-account management — support multiple Instagram business accounts.

Allows running content generation for different brands/accounts
with separate configurations, strategies, and posting schedules.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

ACCOUNTS_FILE = Path(settings.content_output_dir) / "accounts.json"


@dataclass
class AccountConfig:
    """Configuration for a single Instagram account."""

    id: str  # Unique account identifier (slug)
    name: str  # Display name
    instagram_account_id: str = ""
    instagram_access_token: str = ""

    # Content preferences
    language: str = "uz"
    timezone: str = "Asia/Tashkent"
    categories: list[str] = field(default_factory=lambda: [
        "motivational", "educational", "recipe", "travel",
    ])
    content_types: list[str] = field(default_factory=lambda: [
        "reel", "image", "carousel",
    ])
    brand_voice: str = "inspiring, modern, culturally authentic"
    target_audience: str = "Uzbek-speaking Instagram users, 18-35"

    # Posting schedule
    post_times: list[str] = field(default_factory=lambda: ["09:00", "13:00", "18:00"])
    posts_per_day: int = 3

    # Visual identity
    primary_style: str = "photorealistic"
    color_scheme: list[str] = field(default_factory=list)

    # CDN / storage
    cdn_folder: str = ""  # Subfolder in CDN bucket for this account

    active: bool = True


class AccountManager:
    """Manages multiple Instagram accounts."""

    def __init__(self) -> None:
        self._accounts: list[AccountConfig] = []
        self._load()

    def add_account(self, config: AccountConfig) -> None:
        """Register a new account."""
        # Check for duplicate IDs
        if self.get_account(config.id):
            raise ValueError(f"Account '{config.id}' already exists")

        if not config.cdn_folder:
            config.cdn_folder = config.id

        self._accounts.append(config)
        self._save()
        logger.info("accounts.added", id=config.id, name=config.name)

    def get_account(self, account_id: str) -> AccountConfig | None:
        """Get account by ID."""
        for acc in self._accounts:
            if acc.id == account_id:
                return acc
        return None

    def list_accounts(self, active_only: bool = True) -> list[AccountConfig]:
        """List all accounts."""
        if active_only:
            return [a for a in self._accounts if a.active]
        return self._accounts

    def update_account(self, account_id: str, **kwargs) -> AccountConfig | None:
        """Update account settings."""
        acc = self.get_account(account_id)
        if not acc:
            return None

        for key, value in kwargs.items():
            if hasattr(acc, key):
                setattr(acc, key, value)

        self._save()
        logger.info("accounts.updated", id=account_id, fields=list(kwargs.keys()))
        return acc

    def deactivate_account(self, account_id: str) -> bool:
        """Deactivate an account (keeps config for reactivation)."""
        acc = self.get_account(account_id)
        if acc:
            acc.active = False
            self._save()
            logger.info("accounts.deactivated", id=account_id)
            return True
        return False

    def display(self) -> str:
        """Display all accounts."""
        lines = [
            "=" * 65,
            "  Instagram Accounts",
            "=" * 65,
        ]

        if not self._accounts:
            lines.append("  No accounts configured.")
            lines.append("  Use 'python main.py accounts --add' to add one.")
        else:
            for acc in self._accounts:
                status = "Active" if acc.active else "Inactive"
                lines.append(f"\n  [{acc.id}] {acc.name} ({status})")
                lines.append(f"    Language: {acc.language} | TZ: {acc.timezone}")
                lines.append(f"    Schedule: {', '.join(acc.post_times)} ({acc.posts_per_day}/day)")
                lines.append(f"    Categories: {', '.join(acc.categories)}")
                lines.append(f"    Types: {', '.join(acc.content_types)}")
                lines.append(f"    Style: {acc.primary_style}")
                lines.append(f"    Voice: {acc.brand_voice[:50]}")

        lines.append(f"\n{'=' * 65}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        if ACCOUNTS_FILE.exists():
            try:
                data = json.loads(ACCOUNTS_FILE.read_text())
                self._accounts = [AccountConfig(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._accounts = []

    def _save(self) -> None:
        ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(acc) for acc in self._accounts]
        ACCOUNTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
