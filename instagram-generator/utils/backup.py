"""Backup/restore — protect JSON data files.

Backs up:
  - content_queue.json
  - review_queue.json
  - content_calendar.json
  - post_history.json
  - ab_tests.json
  - insights.json
  - token_state.json
  - accounts.json

Supports:
  - Manual backup/restore via CLI
  - Auto-backup before destructive operations
  - Retention policy (keep last N backups)
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

DATA_DIR = Path(settings.content_output_dir)
BACKUP_DIR = DATA_DIR / "backups"

# Files to back up
DATA_FILES = [
    "content_queue.json",
    "review_queue.json",
    "content_calendar.json",
    "post_history.json",
    "ab_tests.json",
    "insights.json",
    "token_state.json",
    "accounts.json",
]


class BackupManager:
    """Backup and restore JSON data files."""

    MAX_BACKUPS = 10  # Keep last N backups

    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = data_dir or DATA_DIR
        self.backup_dir = self.data_dir / "backups"

    def create_backup(self, label: str = "") -> Path:
        """Create a timestamped backup of all data files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{timestamp}_{label}" if label else timestamp
        backup_path = self.backup_dir / name
        backup_path.mkdir(parents=True, exist_ok=True)

        backed_up = []
        for filename in DATA_FILES:
            src = self.data_dir / filename
            if src.exists():
                dst = backup_path / filename
                shutil.copy2(src, dst)
                backed_up.append(filename)

        # Write manifest
        manifest = {
            "created_at": datetime.now().isoformat(),
            "label": label,
            "files": backed_up,
        }
        (backup_path / "manifest.json").write_text(json.dumps(manifest, indent=2))

        logger.info("backup.created", path=str(backup_path), files=len(backed_up))

        # Enforce retention
        self._enforce_retention()

        return backup_path

    def restore_backup(self, backup_name: str) -> int:
        """Restore data files from a backup."""
        backup_path = self.backup_dir / backup_name
        if not backup_path.exists():
            logger.error("backup.not_found", name=backup_name)
            return 0

        # Auto-backup current state before restore
        self.create_backup(label="pre_restore")

        restored = 0
        for filename in DATA_FILES:
            src = backup_path / filename
            if src.exists():
                dst = self.data_dir / filename
                shutil.copy2(src, dst)
                restored += 1

        logger.info("backup.restored", name=backup_name, files=restored)
        return restored

    def list_backups(self) -> list[dict]:
        """List available backups with metadata."""
        if not self.backup_dir.exists():
            return []

        backups = []
        for entry in sorted(self.backup_dir.iterdir(), reverse=True):
            if not entry.is_dir():
                continue

            manifest_file = entry / "manifest.json"
            if manifest_file.exists():
                try:
                    manifest = json.loads(manifest_file.read_text())
                except json.JSONDecodeError:
                    manifest = {}
            else:
                manifest = {}

            files = [f.name for f in entry.iterdir() if f.suffix == ".json" and f.name != "manifest.json"]
            backups.append({
                "name": entry.name,
                "created_at": manifest.get("created_at", ""),
                "label": manifest.get("label", ""),
                "files": len(files),
            })

        return backups

    def display(self) -> str:
        """Display available backups."""
        backups = self.list_backups()
        lines = [
            "=" * 60,
            "  Data Backups",
            "=" * 60,
        ]

        if not backups:
            lines.append("  No backups found.")
        else:
            for b in backups:
                label = f" ({b['label']})" if b["label"] else ""
                lines.append(
                    f"  {b['name']:<28} {b['files']} files{label}"
                )

        lines.append("=" * 60)
        return "\n".join(lines)

    def _enforce_retention(self) -> None:
        """Remove old backups beyond MAX_BACKUPS."""
        if not self.backup_dir.exists():
            return

        backups = sorted(self.backup_dir.iterdir())
        dirs = [d for d in backups if d.is_dir()]

        while len(dirs) > self.MAX_BACKUPS:
            oldest = dirs.pop(0)
            shutil.rmtree(oldest)
            logger.info("backup.pruned", name=oldest.name)
