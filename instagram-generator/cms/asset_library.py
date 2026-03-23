"""Media asset library — organize and reuse generated media.

Features:
  - Tag-based organization
  - Search by tags, category, content type
  - Track which assets have been used and where
  - Automatic metadata extraction (dimensions, size, format)
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)

ASSETS_FILE = Path(settings.content_output_dir) / "asset_library.json"


@dataclass
class MediaAsset:
    """A reusable media file in the library."""

    id: str = ""
    name: str = ""
    file_path: str = ""
    cdn_url: str = ""
    media_type: str = ""  # image, video, audio
    format: str = ""  # png, mp4, mp3
    file_size_bytes: int = 0
    width: int = 0
    height: int = 0
    duration_s: float = 0

    tags: list[str] = field(default_factory=list)
    category: str = ""
    description: str = ""

    # Usage tracking
    used_in: list[str] = field(default_factory=list)  # content IDs
    used_count: int = 0

    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex[:10]
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class AssetLibrary:
    """Manage media assets."""

    def __init__(self) -> None:
        self._assets: list[MediaAsset] = []
        self._load()

    def add(
        self,
        file_path: str,
        name: str = "",
        tags: list[str] | None = None,
        category: str = "",
        cdn_url: str = "",
        description: str = "",
    ) -> MediaAsset:
        """Add a media file to the library."""
        path = Path(file_path)

        # Auto-detect metadata
        media_type = "image"
        if path.suffix.lower() in (".mp4", ".mov", ".avi"):
            media_type = "video"
        elif path.suffix.lower() in (".mp3", ".wav", ".ogg"):
            media_type = "audio"

        size = path.stat().st_size if path.exists() else 0

        width, height = 0, 0
        if media_type == "image" and path.exists():
            try:
                from PIL import Image
                with Image.open(path) as img:
                    width, height = img.size
            except Exception:
                pass

        asset = MediaAsset(
            name=name or path.stem,
            file_path=str(path),
            cdn_url=cdn_url,
            media_type=media_type,
            format=path.suffix.lstrip(".").lower(),
            file_size_bytes=size,
            width=width,
            height=height,
            tags=tags or [],
            category=category,
            description=description,
        )

        self._assets.append(asset)
        self._save()
        logger.info("assets.added", id=asset.id, name=asset.name)
        return asset

    def get(self, asset_id: str) -> MediaAsset | None:
        for a in self._assets:
            if a.id == asset_id:
                return a
        return None

    def search(self, query: str) -> list[MediaAsset]:
        q = query.lower()
        return [
            a for a in self._assets
            if q in a.name.lower()
            or q in a.description.lower()
            or any(q in t.lower() for t in a.tags)
            or q in a.category.lower()
        ]

    def find_by_tags(self, tags: list[str]) -> list[MediaAsset]:
        tag_set = set(t.lower() for t in tags)
        return [
            a for a in self._assets
            if tag_set.intersection(t.lower() for t in a.tags)
        ]

    def find_by_type(self, media_type: str) -> list[MediaAsset]:
        return [a for a in self._assets if a.media_type == media_type]

    def find_unused(self) -> list[MediaAsset]:
        return [a for a in self._assets if a.used_count == 0]

    def mark_used(self, asset_id: str, content_id: str) -> None:
        asset = self.get(asset_id)
        if asset:
            asset.used_in.append(content_id)
            asset.used_count += 1
            asset.updated_at = datetime.now().isoformat()
            self._save()

    def delete(self, asset_id: str) -> bool:
        asset = self.get(asset_id)
        if not asset:
            return False
        self._assets.remove(asset)
        self._save()
        return True

    def get_stats(self) -> dict:
        by_type: dict[str, int] = {}
        total_size = 0
        for a in self._assets:
            by_type[a.media_type] = by_type.get(a.media_type, 0) + 1
            total_size += a.file_size_bytes
        return {
            "total": len(self._assets),
            "by_type": by_type,
            "total_size_mb": round(total_size / (1024 * 1024), 1),
            "unused": len(self.find_unused()),
        }

    def display(self, limit: int = 20) -> str:
        lines = [
            "=" * 70,
            "  Media Asset Library",
            "=" * 70,
        ]

        stats = self.get_stats()
        lines.append(
            f"  Total: {stats['total']} | "
            f"Size: {stats['total_size_mb']}MB | "
            f"Unused: {stats['unused']}"
        )
        type_parts = ", ".join(f"{k}: {v}" for k, v in stats["by_type"].items())
        if type_parts:
            lines.append(f"  Types: {type_parts}")
        lines.append("")

        for asset in self._assets[-limit:]:
            tags = ", ".join(asset.tags[:3]) if asset.tags else "—"
            size = f"{asset.file_size_bytes / 1024:.0f}KB"
            lines.append(
                f"  {asset.id:<10} {asset.media_type:<6} {asset.format:<5} "
                f"{size:<8} used={asset.used_count:<3} "
                f"[{tags}] {asset.name[:25]}"
            )

        lines.append("=" * 70)
        return "\n".join(lines)

    def _load(self) -> None:
        if ASSETS_FILE.exists():
            try:
                data = json.loads(ASSETS_FILE.read_text())
                self._assets = [MediaAsset(**d) for d in data]
            except (json.JSONDecodeError, TypeError):
                self._assets = []

    def _save(self) -> None:
        ASSETS_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(a) for a in self._assets]
        ASSETS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))
