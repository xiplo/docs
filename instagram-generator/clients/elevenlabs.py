"""Eleven Labs API client — Uzbek voiceover generation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = structlog.get_logger(__name__)

OutputFormat = Literal["mp3_44100_128", "mp3_22050_32", "pcm_16000", "pcm_44100"]


class ElevenLabsClient:
    """Text-to-speech in Uzbek via Eleven Labs API."""

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(
        self,
        api_key: str | None = None,
        voice_id: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.elevenlabs_api_key
        self._voice_id = voice_id or settings.elevenlabs_voice_id
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "xi-api-key": self._api_key,
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=20))
    async def synthesize(
        self,
        text: str,
        *,
        voice_id: str | None = None,
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
        style: float = 0.4,
        output_format: OutputFormat = "mp3_44100_128",
    ) -> bytes:
        """Convert Uzbek text to speech, return audio bytes."""
        vid = voice_id or self._voice_id
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": True,
            },
            "language_code": "uz",
        }

        logger.info(
            "elevenlabs.synthesize",
            text_len=len(text),
            voice_id=vid,
            language="uz",
        )

        resp = await self._client.post(
            f"/text-to-speech/{vid}",
            json=payload,
            params={"output_format": output_format},
        )
        resp.raise_for_status()
        return resp.content

    async def save_audio(self, audio_bytes: bytes, output_path: Path) -> Path:
        """Persist audio to disk."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_bytes)
        logger.info("elevenlabs.saved", path=str(output_path))
        return output_path

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    async def list_voices(self) -> list[dict]:
        """Return available voices (useful for finding Uzbek-capable ones)."""
        resp = await self._client.get("/voices")
        resp.raise_for_status()
        return resp.json().get("voices", [])

    async def close(self) -> None:
        await self._client.aclose()
