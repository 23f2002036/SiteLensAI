"""
SiteLens AI — WebSocket frame streaming route

Receives live camera frames over WebSocket, processes them through
the full hazard detection pipeline, and pushes alerts back in real-time.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.hazard.alert_formatter import AlertFormatter
from app.hazard.classifier import HazardClassifier
from app.hazard.prompt_engine import PromptEngine
from app.hazard.safeguards import apply_safeguards

logger = logging.getLogger("sitelens.routes.stream")

router = APIRouter(tags=["streaming"])

# Module-level singletons
_vlm_engine = None
_classifier = HazardClassifier()
_alert_formatter = AlertFormatter()
_prompt_engine = PromptEngine()
_retriever = None
_rule_engine = None


def set_vlm_engine(engine):
    """Called from main.py lifespan to inject the VLM engine."""
    global _vlm_engine
    _vlm_engine = engine


def set_retriever(retriever):
    """Called from main.py lifespan to inject the RAG retriever."""
    global _retriever
    _retriever = retriever


def set_rule_engine(engine):
    """Called from main.py lifespan to inject the rule engine."""
    global _rule_engine
    _rule_engine = engine


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected. Total: %d", len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected. Total: %d", len(self.active_connections))

    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        dead = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except Exception:
                dead.append(conn)
        for conn in dead:
            self.active_connections.remove(conn)


manager = ConnectionManager()


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time frame streaming.

    Protocol:
    - Client sends frames as base64-encoded JSON: {"frame": "<base64>"}
    - Server responds with HazardAlert JSON for every processed frame
    - Frame skip is controlled by config.frame_skip

    The client can also send:
    - {"type": "query", "text": "..."} for worker audio queries
    - {"type": "ping"} for keepalive
    """
    if _vlm_engine is None:
        await websocket.close(code=1013, reason="VLM engine not ready")
        return

    await manager.connect(websocket)
    settings = get_settings()
    frame_counter = 0
    current_worker_query: Optional[str] = None  # holds the latest worker query for VLM

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()

            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON"})
                continue

            # ── Ping ──
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # ── Frame processing ──
            if "frame" in msg:
                frame_counter += 1

                # Skip frames per config
                if frame_counter % settings.frame_skip != 0:
                    await websocket.send_json({
                        "type": "frame_skipped",
                        "frame_number": frame_counter,
                    })
                    continue

                try:
                    image_bytes = base64.b64decode(msg["frame"])
                except Exception:
                    await websocket.send_json({"error": "Invalid base64 frame"})
                    continue

                # Run pipeline
                start = time.time()
                try:
                    vlm_prompt = _prompt_engine.build_vlm_prompt(current_worker_query)
                    vlm_output = await _vlm_engine.analyze_frame(image_bytes, prompt=vlm_prompt)
                    classification = _classifier.classify(vlm_output)

                    # RAG retrieval
                    sop_texts = []
                    if _retriever and classification.hazards:
                        try:
                            rag_query = _prompt_engine.build_rag_query(vlm_output, current_worker_query)
                            rag_results = await _retriever.retrieve(rag_query, top_k=3)
                            sop_texts = [r["content"] for r in rag_results]
                        except Exception:
                            pass

                    # Rule engine
                    if _rule_engine and classification.hazards:
                        try:
                            decision = await _rule_engine.decide(
                                classification=classification,
                                vlm_output=vlm_output,
                                sop_texts=sop_texts,
                            )
                            if decision.used_llm and decision.llm_alert_json:
                                alert = _alert_formatter.from_llm_response(
                                    decision.llm_alert_json, classification
                                )
                            else:
                                alert = _alert_formatter.from_classification(classification)
                        except Exception:
                            alert = _alert_formatter.from_classification(classification)
                    else:
                        alert = _alert_formatter.from_classification(classification)

                    result = alert.to_dict()
                    result = apply_safeguards(result)
                    result["type"] = "alert"
                    result["frame_number"] = frame_counter
                    result["processing_time_ms"] = round((time.time() - start) * 1000)

                    await websocket.send_json(result)

                    # Broadcast to all connections (e.g., supervisor dashboard)
                    if alert.escalate_to_supervisor:
                        await manager.broadcast({
                            "type": "escalation",
                            **result,
                        })

                except Exception as e:
                    logger.exception("Frame processing error")
                    await websocket.send_json({
                        "type": "error",
                        "error": str(e),
                        "frame_number": frame_counter,
                    })

            # ── Worker query ──
            elif msg.get("type") == "query":
                query_text = msg.get("text", "").strip()
                if query_text:
                    current_worker_query = query_text  # inject into next VLM frame analysis
                    await websocket.send_json({
                        "type": "query_ack",
                        "text": query_text,
                        "status": "processing",
                    })
                    # RAG retrieval for voice query
                    if _retriever:
                        try:
                            results = await _retriever.retrieve(query_text, top_k=3)
                            sop_texts = [r["content"][:300] for r in results]
                            answer = "Based on safety procedures: " + " ".join(sop_texts[:2]) if sop_texts else "No SOPs found. Follow standard safety protocols."
                            await websocket.send_json({
                                "type": "query_response",
                                "query": query_text,
                                "answer": answer,
                                "sop_count": len(results),
                            })
                        except Exception as e:
                            await websocket.send_json({
                                "type": "query_error",
                                "error": str(e),
                            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.exception("WebSocket error")
        manager.disconnect(websocket)
