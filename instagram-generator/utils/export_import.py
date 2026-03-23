"""Data export/import — portable format for content and settings.

Exports all CMS data to a single JSON archive:
  - Content items
  - Campaigns
  - Assets metadata
  - Publishing rules
  - Templates
  - Analytics
  - Queue
  - Calendar
  - Post history

Import restores from archive, merging or replacing existing data.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

DATA_DIR = Path(settings.content_output_dir)


class DataExporter:
    """Export all system data to a portable JSON archive."""

    # Files to include in export
    DATA_SOURCES = {
        "cms_content": "cms_content.json",
        "campaigns": "campaigns.json",
        "asset_library": "asset_library.json",
        "publish_rules": "publish_rules.json",
        "content_queue": "content_queue.json",
        "content_calendar": "content_calendar.json",
        "post_history": "post_history.json",
        "ab_tests": "ab_tests.json",
        "review_queue": "review_queue.json",
        "cross_platform_analytics": "cross_platform_analytics.json",
        "insights": "insights.json",
        "accounts": "accounts.json",
    }

    @classmethod
    def export_all(cls, output_path: str = "") -> Path:
        """Export all data to a single JSON file."""
        archive = {
            "version": "2.0.0",
            "exported_at": datetime.now().isoformat(),
            "data": {},
        }

        for key, filename in cls.DATA_SOURCES.items():
            file_path = DATA_DIR / filename
            if file_path.exists():
                try:
                    archive["data"][key] = json.loads(file_path.read_text())
                except json.JSONDecodeError:
                    archive["data"][key] = None
                    logger.warning("export.parse_error", file=filename)

        archive["stats"] = {
            key: len(data) if isinstance(data, list) else 0
            for key, data in archive["data"].items()
            if data is not None
        }

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(DATA_DIR / f"export_{timestamp}.json")

        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(archive, indent=2, ensure_ascii=False))

        logger.info(
            "export.complete",
            path=str(out),
            sources=len(archive["data"]),
        )
        return out

    @classmethod
    def import_all(cls, archive_path: str, merge: bool = False) -> dict:
        """Import data from a JSON archive.

        Args:
            archive_path: Path to the archive file
            merge: If True, merge with existing data. If False, replace.

        Returns:
            Summary of imported data
        """
        path = Path(archive_path)
        if not path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        archive = json.loads(path.read_text())
        data = archive.get("data", {})
        summary = {"imported": [], "skipped": [], "errors": []}

        # Auto-backup before import
        try:
            from utils.backup import BackupManager
            BackupManager().create_backup(label="pre_import")
        except Exception:
            pass

        for key, filename in cls.DATA_SOURCES.items():
            if key not in data or data[key] is None:
                summary["skipped"].append(key)
                continue

            file_path = DATA_DIR / filename
            try:
                if merge and file_path.exists():
                    existing = json.loads(file_path.read_text())
                    if isinstance(existing, list) and isinstance(data[key], list):
                        # Merge lists, deduplicate by 'id' if present
                        existing_ids = {
                            item.get("id") for item in existing
                            if isinstance(item, dict) and "id" in item
                        }
                        for item in data[key]:
                            if isinstance(item, dict) and item.get("id") not in existing_ids:
                                existing.append(item)
                        file_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
                    else:
                        file_path.write_text(json.dumps(data[key], indent=2, ensure_ascii=False))
                else:
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(json.dumps(data[key], indent=2, ensure_ascii=False))

                count = len(data[key]) if isinstance(data[key], list) else 1
                summary["imported"].append(f"{key} ({count} items)")
            except Exception as exc:
                summary["errors"].append(f"{key}: {exc}")

        logger.info(
            "import.complete",
            imported=len(summary["imported"]),
            errors=len(summary["errors"]),
        )
        return summary

    @classmethod
    def display_archive(cls, archive_path: str) -> str:
        """Display contents of an export archive."""
        path = Path(archive_path)
        if not path.exists():
            return f"  Archive not found: {archive_path}"

        archive = json.loads(path.read_text())
        lines = [
            "=" * 60,
            "  Export Archive",
            "=" * 60,
            f"  Version: {archive.get('version', '?')}",
            f"  Exported: {archive.get('exported_at', '?')}",
            f"  Size: {path.stat().st_size / 1024:.1f}KB",
            "",
        ]

        stats = archive.get("stats", {})
        for key, count in sorted(stats.items()):
            lines.append(f"  {key:<30} {count} items")

        lines.append("=" * 60)
        return "\n".join(lines)
