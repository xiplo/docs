"""Content versioning — track edit history for CMS content items.

Every update to a content item creates a version snapshot:
  - Previous state preserved
  - Diff tracking (which fields changed)
  - Rollback to any previous version
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

VERSIONS_FILE = Path(settings.content_output_dir) / "content_versions.json"


@dataclass
class ContentVersion:
    """A historical version of a content item."""

    content_id: str = ""
    version: int = 1
    snapshot: dict = field(default_factory=dict)
    changed_fields: list[str] = field(default_factory=list)
    author: str = ""
    message: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class VersionManager:
    """Track and manage content versions."""

    def __init__(self) -> None:
        self._versions: list[ContentVersion] = []
        self._load()

    def save_version(
        self,
        content_id: str,
        snapshot: dict,
        changed_fields: list[str] | None = None,
        message: str = "",
    ) -> ContentVersion:
        """Save a new version of content."""
        current_version = self.get_latest_version_number(content_id)
        version = ContentVersion(
            content_id=content_id,
            version=current_version + 1,
            snapshot=snapshot,
            changed_fields=changed_fields or [],
            message=message,
        )
        self._versions.append(version)
        self._save()
        logger.info("version.saved", content_id=content_id, version=version.version)
        return version

    def get_versions(self, content_id: str) -> list[ContentVersion]:
        """Get all versions of a content item."""
        return sorted(
            [v for v in self._versions if v.content_id == content_id],
            key=lambda v: v.version,
        )

    def get_version(self, content_id: str, version: int) -> ContentVersion | None:
        for v in self._versions:
            if v.content_id == content_id and v.version == version:
                return v
        return None

    def get_latest(self, content_id: str) -> ContentVersion | None:
        versions = self.get_versions(content_id)
        return versions[-1] if versions else None

    def get_latest_version_number(self, content_id: str) -> int:
        versions = self.get_versions(content_id)
        return versions[-1].version if versions else 0

    def diff(self, content_id: str, v1: int, v2: int) -> dict:
        """Compare two versions and return differences."""
        ver1 = self.get_version(content_id, v1)
        ver2 = self.get_version(content_id, v2)

        if not ver1 or not ver2:
            return {"error": "Version not found"}

        changes = {}
        all_keys = set(ver1.snapshot.keys()) | set(ver2.snapshot.keys())

        for key in all_keys:
            old_val = ver1.snapshot.get(key)
            new_val = ver2.snapshot.get(key)
            if old_val != new_val:
                changes[key] = {"from": old_val, "to": new_val}

        return changes

    def display(self, content_id: str = "") -> str:
        lines = [
            "=" * 65,
            "  Content Version History",
            "=" * 65,
        ]

        if content_id:
            versions = self.get_versions(content_id)
            if not versions:
                lines.append(f"  No versions found for {content_id}")
            else:
                lines.append(f"  Content: {content_id} ({len(versions)} versions)")
                for v in versions:
                    changed = ", ".join(v.changed_fields[:3]) if v.changed_fields else "initial"
                    lines.append(
                        f"    v{v.version:<4} {v.created_at[:19]}  "
                        f"[{changed}]  {v.message[:30]}"
                    )
        else:
            # Show summary
            content_ids = set(v.content_id for v in self._versions)
            lines.append(f"  Tracked: {len(content_ids)} content items, {len(self._versions)} total versions")
            for cid in sorted(content_ids):
                count = len([v for v in self._versions if v.content_id == cid])
                latest = self.get_latest(cid)
                lines.append(
                    f"    {cid:<12} {count} versions  "
                    f"last: {latest.created_at[:10] if latest else '?'}"
                )

        lines.append("=" * 65)
        return "\n".join(lines)

    def _load(self) -> None:
        if VERSIONS_FILE.exists():
            try:
                data = json.loads(VERSIONS_FILE.read_text())
                self._versions = [ContentVersion(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._versions = []

    def _save(self) -> None:
        VERSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(v) for v in self._versions]
        VERSIONS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
