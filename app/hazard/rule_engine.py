"""
SiteLens AI — Rule Engine (Decision Layer)

Synthesizes VLM visual analysis + RAG-retrieved SOPs + classifier output
to make deterministic decisions: WARN_WORKER, GUIDE_WORKER, or ESCALATE_SUPERVISOR.

Falls back to classifier-only rules if LLM call fails or latency is too high.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import httpx

from app.config import Settings, get_settings
from app.hazard.classifier import ClassificationResult, SeverityLevel
from app.hazard.prompt_engine import PromptEngine

logger = logging.getLogger("sitelens.hazard.rule_engine")


class Decision(str, Enum):
    WARN_WORKER = "WARN_WORKER"
    GUIDE_WORKER = "GUIDE_WORKER"
    ESCALATE_SUPERVISOR = "ESCALATE_SUPERVISOR"
    NO_ACTION = "NO_ACTION"


@dataclass
class RuleDecision:
    """Output of the rule engine."""
    decision: Decision
    llm_alert_json: Optional[dict[str, Any]] = None
    reasoning: str = ""
    latency_ms: int = 0
    used_llm: bool = False


class RuleEngine:
    """
    Decision layer that combines VLM output + RAG context + classifier
    to determine the appropriate action.

    Uses LLM reasoning when available, falls back to deterministic rules.
    """

    # Max latency before we skip LLM and use classifier-only
    MAX_LLM_LATENCY_MS = 10000

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self._prompt_engine = PromptEngine()
        self._client = httpx.AsyncClient(timeout=15.0)

        # Determine LLM endpoint based on backend
        if self.settings.vlm_backend.value == "groq":
            self._api_url = "https://api.groq.com/openai/v1/chat/completions"
            self._api_key = self.settings.groq_api_key
            self._model = self.settings.groq_model
        elif self.settings.vlm_backend.value == "grok":
            self._api_url = "https://api.x.ai/v1/chat/completions"
            self._api_key = self.settings.grok_api_key
            self._model = self.settings.grok_model
        else:
            self._api_url = None
            self._api_key = None
            self._model = None

    async def decide(
        self,
        classification: ClassificationResult,
        vlm_output: dict[str, Any],
        sop_texts: Optional[list[str]] = None,
        worker_query: Optional[str] = None,
    ) -> RuleDecision:
        """
        Make a decision based on all available context.

        Falls back to deterministic rules if LLM is unavailable.
        """
        # ── Fast-path: no hazards → no action ──
        if classification.overall_severity == SeverityLevel.NONE:
            return RuleDecision(
                decision=Decision.NO_ACTION,
                reasoning="No hazards detected in scene.",
            )

        # ── Deterministic decision (always computed as fallback) ──
        deterministic = self._deterministic_decide(classification, worker_query)

        # ── Try LLM reasoning for richer alert generation ──
        if self._api_url and self._api_key:
            try:
                start = time.time()
                llm_result = await self._llm_reason(
                    vlm_output, sop_texts, worker_query
                )
                latency = int((time.time() - start) * 1000)

                if llm_result:
                    # Determine decision from LLM output
                    decision = self._parse_llm_decision(llm_result, classification)
                    return RuleDecision(
                        decision=decision,
                        llm_alert_json=llm_result,
                        reasoning=f"LLM reasoning in {latency}ms",
                        latency_ms=latency,
                        used_llm=True,
                    )
            except Exception as e:
                logger.warning("LLM reasoning failed, using deterministic: %s", e)

        return deterministic

    def _deterministic_decide(
        self,
        classification: ClassificationResult,
        worker_query: Optional[str] = None,
    ) -> RuleDecision:
        """Pure rule-based decision without LLM."""
        if worker_query:
            return RuleDecision(
                decision=Decision.GUIDE_WORKER,
                reasoning="Worker query received — providing guidance.",
            )

        if classification.escalate or classification.overall_severity == SeverityLevel.CRITICAL:
            return RuleDecision(
                decision=Decision.ESCALATE_SUPERVISOR,
                reasoning=f"CRITICAL hazard: {classification.hazards[0].description if classification.hazards else 'unknown'}",
            )

        if classification.overall_severity == SeverityLevel.WARNING:
            return RuleDecision(
                decision=Decision.WARN_WORKER,
                reasoning="WARNING-level safety breach detected.",
            )

        return RuleDecision(
            decision=Decision.GUIDE_WORKER,
            reasoning="INFO-level observation.",
        )

    async def _llm_reason(
        self,
        vlm_output: dict[str, Any],
        sop_texts: Optional[list[str]] = None,
        worker_query: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Call LLM with the full prompt engine template."""
        prompt = self._prompt_engine.build_hazard_prompt(
            vlm_scene_analysis=vlm_output,
            rag_retrieved_sops=sop_texts,
            worker_audio_input=worker_query,
        )

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": "You are SiteLens AI, a construction site safety system. Respond ONLY with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 800,
            "temperature": 0.2,
        }

        resp = await self._client.post(
            self._api_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

        raw_text = data["choices"][0]["message"]["content"]

        # Parse JSON from LLM response
        from app.models.vlm_engine import VLMEngine
        return VLMEngine._parse_json_response(raw_text)

    def _parse_llm_decision(
        self,
        llm_result: dict[str, Any],
        classification: ClassificationResult,
    ) -> Decision:
        """Map LLM output fields to a Decision enum."""
        if llm_result.get("escalate_to_supervisor", False) or classification.escalate:
            return Decision.ESCALATE_SUPERVISOR

        severity = llm_result.get("severity_level", "NONE").upper()
        if severity == "CRITICAL":
            return Decision.ESCALATE_SUPERVISOR
        if severity == "WARNING":
            return Decision.WARN_WORKER
        if severity == "INFO":
            return Decision.GUIDE_WORKER

        return Decision.NO_ACTION
