"""
SiteLens AI — Alert history & SSE endpoints

Provides alert history storage, retrieval, and Server-Sent Events
streaming for the supervisor dashboard.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

logger = logging.getLogger("sitelens.routes.alerts")

router = APIRouter(prefix="/api", tags=["alerts"])

# In-memory alert store (replace with DB in production)
_alert_history: deque[dict[str, Any]] = deque(maxlen=500)
_sse_subscribers: list[asyncio.Queue] = []
_audit_db = None


def set_audit_db(db):
    """Called from main.py lifespan to inject the audit database."""
    global _audit_db
    _audit_db = db


def record_alert(alert: dict[str, Any]):
    """Store an alert in history and notify SSE subscribers."""
    alert["recorded_at"] = datetime.now(timezone.utc).isoformat()
    _alert_history.appendleft(alert)

    # Notify SSE subscribers
    dead = []
    for q in _sse_subscribers:
        try:
            q.put_nowait(alert)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _sse_subscribers.remove(q)


@router.get("/alerts")
async def get_alerts(
    limit: int = 50,
    severity: str | None = None,
):
    """
    Get recent alert history.

    Query params:
      - limit: max alerts to return (default 50)
      - severity: filter by CRITICAL / WARNING / INFO
    """
    alerts = list(_alert_history)

    if severity:
        alerts = [a for a in alerts if a.get("severity_level") == severity.upper()]

    return {
        "alerts": alerts[:limit],
        "total": len(alerts),
    }


@router.get("/alerts/stream")
async def alert_stream(request: Request):
    """
    Server-Sent Events stream for real-time alert updates.
    Used by the supervisor dashboard.
    """

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        _sse_subscribers.append(queue)
        try:
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                try:
                    alert = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(alert)}\n\n"
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        finally:
            if queue in _sse_subscribers:
                _sse_subscribers.remove(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/alerts/escalate")
async def escalate_alert(alert_id: str):
    """Manually escalate an alert to supervisor level."""
    for alert in _alert_history:
        if alert.get("alert_id") == alert_id:
            alert["escalate_to_supervisor"] = True
            alert["manually_escalated"] = True
            alert["escalated_at"] = datetime.now(timezone.utc).isoformat()
            record_alert(alert)  # Notify SSE
            return {"status": "escalated", "alert_id": alert_id}

    return {"status": "not_found", "alert_id": alert_id}
