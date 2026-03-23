"""Webhook server — receives Instagram insights and external triggers.

Endpoints:
  GET  /health              — Health check
  GET  /status              — Queue stats + circuit breakers + token status
  GET  /queue               — View content queue
  GET  /calendar            — View content calendar
  GET  /analytics           — View analytics report
  GET  /trends              — Current trending topics
  GET  /review              — Content review queue
  POST /webhook/instagram   — Instagram webhook (insights updates)
  POST /trigger/generate    — Trigger content generation via HTTP
  POST /trigger/trends      — Auto-enqueue trending topics
  POST /review/approve/:id  — Approve content for publishing
  POST /review/reject/:id   — Reject content
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
    """Start the webhook HTTP server using raw asyncio."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading

    class WebhookHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            # Auth check for non-public endpoints
            if self.path != "/health":
                from utils.auth import check_api_key
                if not check_api_key(self.headers):
                    self._respond(401, {"error": "Unauthorized — set X-API-Key header"})
                    return

            if self.path == "/health":
                self._respond(200, {
                    "status": "ok",
                    "timestamp": datetime.now().isoformat(),
                    "version": "2.0.0",
                })

            elif self.path == "/status":
                from pipeline.queue import ContentQueue
                from utils.circuit_breaker import CIRCUIT_BREAKERS

                queue = ContentQueue()
                breakers = {
                    name: cb.get_status()
                    for name, cb in CIRCUIT_BREAKERS.items()
                }

                # Token status
                try:
                    from utils.token_refresh import TokenRefresher
                    token_status = TokenRefresher().get_status()
                except Exception:
                    token_status = {"configured": False}

                self._respond(200, {
                    "status": "running",
                    "queue": queue.get_stats(),
                    "pending": queue.get_pending_count(),
                    "circuit_breakers": breakers,
                    "token": token_status,
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

            elif self.path == "/trends":
                from strategy.trends import TrendEngine
                self._respond_text(200, TrendEngine.display_trends())

            elif self.path == "/review":
                from pipeline.approval import ApprovalWorkflow
                workflow = ApprovalWorkflow()
                self._respond_text(200, workflow.display())

            elif self.path == "/metrics":
                from utils.metrics import metrics as m
                self._respond_text(200, m.export_prometheus())

            elif self.path == "/hashtags":
                from skills.hashtags import HashtagResearch
                self._respond_text(200, HashtagResearch.display())

            elif self.path == "/library":
                from templates.library import TemplateLibrary
                self._respond_text(200, TemplateLibrary.display())

            else:
                self._respond(404, {"error": "Not found"})

        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length) if content_length else b""

            # Auth check for trigger/review endpoints (Instagram webhook uses HMAC)
            if self.path != "/webhook/instagram":
                from utils.auth import check_api_key
                if not check_api_key(self.headers):
                    self._respond(401, {"error": "Unauthorized — set X-API-Key header"})
                    return

            if self.path == "/webhook/instagram":
                self._handle_instagram_webhook(body)

            elif self.path == "/trigger/generate":
                self._handle_trigger(body)

            elif self.path == "/trigger/trends":
                self._handle_trends_enqueue()

            elif self.path.startswith("/review/approve/"):
                item_id = self.path.split("/")[-1]
                self._handle_review_action(item_id, "approve", body)

            elif self.path.startswith("/review/reject/"):
                item_id = self.path.split("/")[-1]
                self._handle_review_action(item_id, "reject", body)

            else:
                self._respond(404, {"error": "Not found"})

        def _handle_instagram_webhook(self, body: bytes):
            """Process Instagram webhook payload."""
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

            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    field_name = change.get("field", "")
                    value = change.get("value", {})

                    if field_name == "insights":
                        self._process_insights(value)
                    elif field_name == "comments":
                        logger.info("webhook.comment", data=value)
                    elif field_name == "mentions":
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

        def _handle_trends_enqueue(self):
            """Auto-enqueue current trending topics."""
            from strategy.trends import TrendEngine
            from pipeline.queue import ContentQueue

            trends = TrendEngine.get_current_trends(limit=5)
            queue = ContentQueue()
            enqueued = []

            for trend in trends:
                suggestion = TrendEngine.suggest_content_for_trend(trend)
                item = queue.enqueue(
                    topic=suggestion["topic"],
                    category=suggestion["category"],
                    content_type=suggestion["content_type"],
                    priority=suggestion["priority"],
                )
                enqueued.append({
                    "id": item.id,
                    "topic": suggestion["topic"],
                    "priority": suggestion["priority"],
                })

            self._respond(200, {
                "status": "enqueued",
                "count": len(enqueued),
                "items": enqueued,
            })

        def _handle_review_action(self, item_id: str, action: str, body: bytes):
            """Approve or reject a review item."""
            from pipeline.approval import ApprovalWorkflow

            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                data = {}

            workflow = ApprovalWorkflow()
            notes = data.get("notes", "")

            if action == "approve":
                item = workflow.approve(item_id, notes)
                if item:
                    # Move approved item to publish queue
                    from pipeline.queue import ContentQueue
                    queue = ContentQueue()
                    queue.enqueue(
                        topic=item.topic,
                        category=item.category,
                        content_type=item.content_type,
                        priority=9,  # High priority for approved content
                    )
                    self._respond(200, {"status": "approved", "id": item_id})
                else:
                    self._respond(404, {"error": f"Review item {item_id} not found or not pending"})

            elif action == "reject":
                item = workflow.reject(item_id, notes)
                if item:
                    self._respond(200, {"status": "rejected", "id": item_id})
                else:
                    self._respond(404, {"error": f"Review item {item_id} not found or not pending"})

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

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        server.shutdown()
