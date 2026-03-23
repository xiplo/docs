"""YouTube Shorts API client — upload short-form videos."""

from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class YouTubeClient:
    """Upload videos to YouTube (Shorts) via the Data API v3."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"
    UPLOAD_URL = "https://www.googleapis.com/upload/youtube/v3/videos"

    def __init__(self, access_token: str = "", api_key: str = "") -> None:
        self._token = access_token
        self._api_key = api_key
        self._client = httpx.AsyncClient(
            timeout=300.0,
            headers={"Authorization": f"Bearer {self._token}"} if access_token else {},
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def upload_short(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        *,
        category_id: str = "22",  # People & Blogs
        privacy: str = "public",
    ) -> str:
        """Upload a video as a YouTube Short. Returns video ID."""
        # #Shorts in title signals YouTube to treat it as Short
        if "#Shorts" not in title and "#shorts" not in title:
            title = f"{title} #Shorts"

        metadata = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": False,
            },
        }

        # Resumable upload
        init_resp = await self._client.post(
            self.UPLOAD_URL,
            params={
                "uploadType": "resumable",
                "part": "snippet,status",
            },
            json=metadata,
        )
        init_resp.raise_for_status()
        upload_url = init_resp.headers.get("Location", "")

        if not upload_url:
            raise RuntimeError("YouTube did not return upload URL")

        # Upload video bytes
        with open(video_path, "rb") as f:
            video_data = f.read()

        upload_resp = await self._client.put(
            upload_url,
            content=video_data,
            headers={"Content-Type": "video/mp4"},
        )
        upload_resp.raise_for_status()
        video_id = upload_resp.json()["id"]

        logger.info("youtube.uploaded", video_id=video_id, title=title[:50])
        return video_id

    async def get_video_stats(self, video_id: str) -> dict:
        """Get video statistics."""
        resp = await self._client.get(
            f"{self.BASE_URL}/videos",
            params={
                "part": "statistics",
                "id": video_id,
                "key": self._api_key,
            },
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return items[0]["statistics"] if items else {}

    async def close(self) -> None:
        await self._client.aclose()
