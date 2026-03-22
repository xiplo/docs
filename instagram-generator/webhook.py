"""Webhook server — receives Instagram insights and external triggers.

Endpoints:
  GET  /health              — Health check
  GET  /status              — Queue stats + scheduler status
  POST /webhook/instagram   — Instagram webhook (insights updates)
  POST /trigger/generate    — Trigger content generation via HTTP
  GET  /queue               — View content queue
  GET  /calendar            — View content calendar
  GET  /analytics           — View analytics report
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import datetime

import structlog

from config import settings

logger = structlog.get_logger(__name__)


async def start_webhook_server(port: int = 8080) -> None:
    """Start the webhook HTTP server using raw asyncio (no framework dependency)."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class WebhookHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                self._respond(200, {"status": "ok", "timestamp": datetime.now().isoformat()})

            elif self.path == "/status":
                from pipeline.queue import ContentQueue
                queue = ContentQueue()
                self._respond(200, {
                    "status": "running",
                    "queue": queue.get_stats(),
                    "pending": queue.get_pending_count(),
                })

            elif self.path == "/queue":
                from pipeline.queue import ContentQueue
                queue = ContentQueue()
                self._respond_text(200, queue.display())

            elif self.path == "/calendar":
                from strategy.calendar import ContentCalendar
                cal = ContentCalendar()
                cal.load()
                self._respond_text(200, cal.display())

            elif self.path == "/analytics":
                from skills.analytics import AnalyticsSkills
                self._respond_text(200, AnalyticsSkills.generate_report())

            else:
                self._respond(404, {"error": "Not found"})

        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""

            if self.path == "/webhook/instagram":
                self._handle_instagram_webhook(body)

            elif self.path == "/trigger/generate":
                self._handle_trigger(body)

            else:
                self._respond(404, {"error": "Not found"})

        def _handle_instagram_webhook(self, body: bytes):
            """Process Instagram webhook payload (insights, comments, etc.)."""
            # Verify webhook signature if secret is configured
            if settings.webhook_secret:
                signature = self.headers.get("X-Hub-Signature-256", "")
                expected = "sha256=" + hmac.new(
                    settings.webhook_secret.encode(),
                    body,
                    hashlib.sha256,
                ).hexdigest()
                if not hmac.compare_digest(signature, expected):
                    logger.warning("webhook.invalid_signature")
                    self._respond(403, {"error": "Invalid signature"})
                    return

            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._respond(400, {"error": "Invalid JSON"})
                return

            logger.info("webhook.instagram", payload_keys=list(data.keys()))

            # Process webhook entries
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    field = change.get("field", "")
                    value = change.get("value", {})

                    if field == "insights":
                        self._process_insights(value)
                    elif field == "comments":
                        logger.info("webhook.comment", data=value)
                    elif field == "mentions":
                        logger.info("webhook.mention", data=value)

            self._respond(200, {"status": "received"})

        def _handle_trigger(self, body: bytes):
            """Handle external trigger to generate content."""
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._respond(400, {"error": "Invalid JSON"})
                return

            topic = data.get("topic", "")
            category = data.get("category", "motivational")
            content_type = data.get("content_type", "reel")

            if not topic:
                self._respond(400, {"error": "topic is required"})
                return

            # Enqueue the content request
            from pipeline.queue import ContentQueue
            queue = ContentQueue()
            item = queue.enqueue(
                topic=topic,
                category=category,
                content_type=content_type,
                priority=data.get("priority", 7),
            )

            self._respond(202, {
                "status": "queued",
                "id": item.id,
                "topic": topic,
            })

        def _process_insights(self, value: dict):
            """Store Instagram insights for analytics."""
            insights_file = settings.content_output_dir / "insights.json"
            insights_file.parent.mkdir(parents=True, exist_ok=True)

            existing = []
            if insights_file.exists():
                try:
                    existing = json.loads(insights_file.read_text())
                except json.JSONDecodeError:
                    existing = []

            existing.append({
                "timestamp": datetime.now().isoformat(),
                "data": value,
            })

            insights_file.write_text(json.dumps(existing, indent=2))
            logger.info("webhook.insights_stored", count=len(existing))

        def _respond(self, code: int, data: dict):
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

        def _respond_text(self, code: int, text: str):
            self.send_response(code)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(text.encode())

        def log_message(self, format, *args):
            logger.info("webhook.request", message=format % args)

    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    logger.info("webhook.start", port=port)

    # Run in thread to not block asyncio
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        server.shutdown()
