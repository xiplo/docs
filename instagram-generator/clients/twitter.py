"""Twitter/X API client — post tweets, threads, and media."""

from __future__ import annotations

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

logger = structlog.get_logger(__name__)


class TwitterClient:
    """Publish content to Twitter/X via the v2 API."""

    BASE_URL = "https://api.twitter.com/2"

    def __init__(
        self,
        bearer_token: str = "",
        api_key: str = "",
        api_secret: str = "",
        access_token: str = "",
        access_secret: str = "",
    ) -> None:
        self._bearer = bearer_token
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=60.0,
            headers={"Authorization": f"Bearer {self._bearer}"} if bearer_token else {},
        )
        # For OAuth 1.0a (required for posting)
        self._api_key = api_key
        self._api_secret = api_secret
        self._access_token = access_token
        self._access_secret = access_secret

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    async def post_tweet(self, text: str, media_ids: list[str] | None = None) -> str:
        """Post a tweet. Returns tweet ID."""
        payload: dict = {"text": text}
        if media_ids:
            payload["media"] = {"media_ids": media_ids}

        resp = await self._client.post("/tweets", json=payload)
        resp.raise_for_status()
        data = resp.json()
        tweet_id = data["data"]["id"]
        logger.info("twitter.posted", tweet_id=tweet_id)
        return tweet_id

    async def post_thread(self, tweets: list[str]) -> list[str]:
        """Post a thread of tweets. Returns list of tweet IDs."""
        ids = []
        reply_to = None
        for text in tweets:
            payload: dict = {"text": text}
            if reply_to:
                payload["reply"] = {"in_reply_to_tweet_id": reply_to}

            resp = await self._client.post("/tweets", json=payload)
            resp.raise_for_status()
            tweet_id = resp.json()["data"]["id"]
            ids.append(tweet_id)
            reply_to = tweet_id

        logger.info("twitter.thread_posted", count=len(ids))
        return ids

    async def upload_media(self, file_path: str, media_type: str = "image") -> str:
        """Upload media for attachment. Returns media_id."""
        upload_url = "https://upload.twitter.com/1.1/media/upload.json"
        async with httpx.AsyncClient(timeout=120.0) as client:
            with open(file_path, "rb") as f:
                files = {"media": f}
                resp = await client.post(upload_url, files=files)
                resp.raise_for_status()
                media_id = resp.json()["media_id_string"]
                logger.info("twitter.media_uploaded", media_id=media_id)
                return media_id

    async def close(self) -> None:
        await self._client.aclose()
