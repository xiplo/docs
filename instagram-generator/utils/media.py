"""Media utilities — audio/video merge, text overlays."""

from __future__ import annotations

import subprocess
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def merge_audio_video(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
) -> Path:
    """Merge an audio track (Uzbek voiceover) with a video using ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(output_path),
    ]
    logger.info("ffmpeg.merge", video=str(video_path), audio=str(audio_path))
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def add_text_overlay(
    video_path: Path,
    text: str,
    output_path: Path,
    *,
    font_size: int = 48,
    font_color: str = "white",
    position: str = "center",
    bg_opacity: float = 0.6,
) -> Path:
    """Burn Uzbek text subtitles/overlay onto a video via ffmpeg."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Escape special chars for ffmpeg drawtext
    safe_text = text.replace("'", "\\'").replace(":", "\\:")

    # Position mapping
    pos_map = {
        "center": "x=(w-text_w)/2:y=(h-text_h)/2",
        "bottom": "x=(w-text_w)/2:y=h-text_h-60",
        "top": "x=(w-text_w)/2:y=60",
    }
    xy = pos_map.get(position, pos_map["bottom"])

    vf = (
        f"drawtext=text='{safe_text}'"
        f":fontsize={font_size}"
        f":fontcolor={font_color}"
        f":box=1:boxcolor=black@{bg_opacity}:boxborderw=12"
        f":{xy}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", vf,
        "-c:a", "copy",
        str(output_path),
    ]
    logger.info("ffmpeg.overlay", text=text[:40])
    subprocess.run(cmd, check=True, capture_output=True)
    return output_path
