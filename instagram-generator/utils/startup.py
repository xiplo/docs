"""Startup validation and diagnostics.

Validates environment, API connectivity, and system dependencies
before the application starts processing content.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import structlog

from config import settings

logger = structlog.get_logger(__name__)


@dataclass
class CheckResult:
    name: str
    passed: bool
    message: str
    critical: bool = True


@dataclass
class StartupReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks if c.critical)

    def display(self) -> str:
        lines = [
            "=" * 55,
            "  Startup Diagnostics",
            "=" * 55,
        ]
        for check in self.checks:
            icon = "[+]" if check.passed else "[!]" if check.critical else "[~]"
            lines.append(f"  {icon} {check.name}: {check.message}")

        status = "READY" if self.passed else "BLOCKED"
        lines.append(f"\n  Status: {status}")
        lines.append("=" * 55)
        return "\n".join(lines)


def validate_environment(require_all: bool = False) -> StartupReport:
    """Run all startup checks and return a report."""
    report = StartupReport()

    # Python version
    v = sys.version_info
    report.checks.append(CheckResult(
        "Python",
        v >= (3, 11),
        f"{v.major}.{v.minor}.{v.micro}" + (" (need 3.11+)" if v < (3, 11) else ""),
        critical=True,
    ))

    # ffmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    report.checks.append(CheckResult(
        "ffmpeg",
        ffmpeg_path is not None,
        ffmpeg_path or "NOT FOUND — install ffmpeg for video processing",
        critical=True,
    ))

    # Output directory
    output_dir = Path(settings.content_output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        report.checks.append(CheckResult(
            "Output dir",
            True,
            str(output_dir),
        ))
    except PermissionError:
        report.checks.append(CheckResult(
            "Output dir",
            False,
            f"Cannot create {output_dir} — permission denied",
        ))

    # API keys
    api_checks = [
        ("Nano Banana API", settings.nano_banana_api_key, True),
        ("Kling API", settings.kling_api_key, True),
        ("ElevenLabs API", settings.elevenlabs_api_key, True),
        ("ElevenLabs Voice", settings.elevenlabs_voice_id, True),
        ("Instagram Token", settings.instagram_access_token, True),
        ("Instagram Account", settings.instagram_business_account_id, True),
    ]

    for name, value, critical in api_checks:
        has_value = bool(value and value.strip())
        report.checks.append(CheckResult(
            name,
            has_value,
            "configured" if has_value else "MISSING",
            critical=critical if require_all else False,
        ))

    # CDN configuration
    cdn = settings.cdn_provider
    if cdn in ("s3", "r2", "minio"):
        has_bucket = bool(settings.cdn_bucket_name)
        has_creds = bool(settings.aws_access_key_id)
        report.checks.append(CheckResult(
            f"CDN ({cdn})",
            has_bucket and has_creds,
            "configured" if (has_bucket and has_creds) else "bucket or credentials missing",
            critical=False,
        ))
    elif cdn == "http":
        has_url = bool(settings.cdn_upload_url)
        report.checks.append(CheckResult(
            "CDN (http)",
            has_url,
            "configured" if has_url else "CDN_UPLOAD_URL missing",
            critical=False,
        ))

    # Timezone
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(settings.timezone)
        report.checks.append(CheckResult(
            "Timezone",
            True,
            settings.timezone,
        ))
    except (KeyError, ImportError):
        report.checks.append(CheckResult(
            "Timezone",
            False,
            f"Invalid timezone: {settings.timezone}",
        ))

    if not report.passed:
        logger.error("startup.validation_failed", checks=[
            {"name": c.name, "passed": c.passed, "message": c.message}
            for c in report.checks if not c.passed
        ])

    return report
