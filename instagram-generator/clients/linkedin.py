"""LinkedIn API client — post to LinkedIn pages and profiles."""

from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class LinkedInClient:
    """Publish content to LinkedIn via the Marketing API."""

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(
        self,
        access_token: str = "",
        organization_id: str = "",
        person_id: str = "",
    ) -> None:
        self._token = access_token
        self._org_id = organization_id
        self._person_id = person_id
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=120.0,
            headers={"Authorization": f"Bearer {self._token}"},
        )

    @property
    def _author(self) -> str:
        if self._org_id:
            return f"urn:li:organization:{self._org_id}"
        return f"urn:li:person:{self._person_id}"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_text(self, text: str) -> str:
        """Post a text update. Returns share URN."""
        payload = {
            "author": self._author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "NONE",
                },
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        resp = await self._client.post("/ugcPosts", json=payload)
        resp.raise_for_status()
        share_id = resp.headers.get("x-restli-id", resp.json().get("id", ""))
        logger.info("linkedin.posted_text", share_id=share_id)
        return share_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_image(
        self, image_url: str, text: str = ""
    ) -> str:
        """Post with an image. Returns share URN."""
        payload = {
            "author": self._author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status": "READY",
                        "originalUrl": image_url,
                    }],
                },
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        resp = await self._client.post("/ugcPosts", json=payload)
        resp.raise_for_status()
        share_id = resp.headers.get("x-restli-id", "")
        logger.info("linkedin.posted_image", share_id=share_id)
        return share_id

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_article(
        self, url: str, title: str = "", description: str = "", text: str = ""
    ) -> str:
        """Share an article/link. Returns share URN."""
        payload = {
            "author": self._author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "originalUrl": url,
                        "title": {"text": title},
                        "description": {"text": description},
                    }],
                },
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        resp = await self._client.post("/ugcPosts", json=payload)
        resp.raise_for_status()
        share_id = resp.headers.get("x-restli-id", "")
        logger.info("linkedin.posted_article", share_id=share_id)
        return share_id

    async def close(self) -> None:
        await self._client.aclose()
