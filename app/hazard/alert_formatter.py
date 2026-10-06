"""
SiteLens AI — Alert Formatter

Parses VLM / LLM responses into validated HazardAlert dataclasses
and enforces output constraints (word limits, required fields, etc.).
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from app.hazard.classifier import (
    ClassificationResult,
    HazardType,
    SeverityLevel,
)

logger = logging.getLogger("sitelens.hazard.alert")


# ── Alert data class ────────────────────────────────────────────────────

@dataclass
class HazardAlert:
    """
    Final structured alert object matching the JSON output format
    defined in the architecture document.
    """

    alert_id: str = field(default_factory=lambda: uuid4().hex[:12])
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    hazard_detected: bool = False
    severity_level: str = "NONE"
    hazard_type: str = "General"
    audio_alert_text: str = ""
    hud_display_card: str = ""
    sop_reference: str = ""
    escalate_to_supervisor: bool = False
    recommended_action: str = ""

    # Extra metadata
    scene_description: str = ""
    worker_count: int = 0
    hazards_detail: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


# ── Formatter ────────────────────────────────────────────────────────────

class AlertFormatter:
    """
    Converts a ClassificationResult + optional LLM-generated alert JSON
    into a validated HazardAlert.
    """

    def __init__(self, max_audio_words: int = 25):
        self.max_audio_words = max_audio_words

    # ── from classification only ──

    def from_classification(
        self,
        classification: ClassificationResult,
    ) -> HazardAlert:
        """
        Build a HazardAlert directly from the classifier output
        (without a secondary LLM call for the prompt engine).
        """
        alert = HazardAlert(
            hazard_detected=classification.overall_severity != SeverityLevel.NONE,
            severity_level=classification.overall_severity.value,
            scene_description=classification.scene_description,
            worker_count=classification.worker_count,
            escalate_to_supervisor=classification.escalate,
        )

        if classification.hazards:
            # Primary hazard is the most severe one
            primary = max(
                classification.hazards,
                key=lambda h: {
                    SeverityLevel.CRITICAL: 3,
                    SeverityLevel.WARNING: 2,
                    SeverityLevel.INFO: 1,
                    SeverityLevel.NONE: 0,
                }.get(h.severity, 0),
            )
            alert.hazard_type = primary.hazard_type.value
            alert.audio_alert_text = self._generate_audio_text(
                primary, classification.overall_severity
            )
            alert.hud_display_card = self._generate_hud_card(classification)
            alert.recommended_action = self._generate_recommendation(
                primary, classification
            )
            alert.hazards_detail = [
                {
                    "type": h.hazard_type.value,
                    "description": h.description,
                    "location": h.location,
                    "severity": h.severity.value,
                    "worker_in_danger": h.worker_in_danger,
                }
                for h in classification.hazards
            ]

        return alert

    # ── from LLM JSON response ──

    def from_llm_response(
        self,
        llm_json: dict[str, Any],
        classification: ClassificationResult,
    ) -> HazardAlert:
        """
        Parse the LLM-generated strict JSON alert and merge with
        classification metadata.
        """
        alert = HazardAlert(
            hazard_detected=llm_json.get("hazard_detected", False),
            severity_level=llm_json.get("severity_level", "NONE"),
            hazard_type=llm_json.get("hazard_type", "General"),
            audio_alert_text=llm_json.get("audio_alert_text", ""),
            hud_display_card=llm_json.get("hud_display_card", ""),
            sop_reference=llm_json.get("sop_reference", ""),
            escalate_to_supervisor=llm_json.get("escalate_to_supervisor", False),
            recommended_action=llm_json.get("recommended_action", ""),
            scene_description=classification.scene_description,
            worker_count=classification.worker_count,
            hazards_detail=[
                {
                    "type": h.hazard_type.value,
                    "description": h.description,
                    "location": h.location,
                    "severity": h.severity.value,
                    "worker_in_danger": h.worker_in_danger,
                }
                for h in classification.hazards
            ],
        )

        # Enforce audio word limit
        alert.audio_alert_text = self._enforce_word_limit(
            alert.audio_alert_text, alert.severity_level
        )

        # Override escalation if classifier says so
        if classification.escalate:
            alert.escalate_to_supervisor = True

        # ── Safety override: if classifier found hazards the LLM missed, inject them ──
        if classification.hazards and not alert.hazard_detected:
            logger.warning(
                "LLM said no hazard but classifier found %d hazard(s) — overriding.",
                len(classification.hazards),
            )
            alert.hazard_detected = True
            alert.severity_level = classification.overall_severity.value
            primary = max(
                classification.hazards,
                key=lambda h: {
                    SeverityLevel.CRITICAL: 3,
                    SeverityLevel.WARNING: 2,
                    SeverityLevel.INFO: 1,
                    SeverityLevel.NONE: 0,
                }.get(h.severity, 0),
            )
            if not alert.audio_alert_text:
                alert.audio_alert_text = self._generate_audio_text(
                    primary, classification.overall_severity
                )
            if not alert.hud_display_card or alert.hud_display_card == "No HUD data":
                alert.hud_display_card = self._generate_hud_card(classification)
            if not alert.recommended_action:
                alert.recommended_action = self._generate_recommendation(
                    primary, classification
                )
            alert.hazard_type = primary.hazard_type.value

        # Always include all classifier hazards in detail list
        if classification.hazards:
            alert.hazards_detail = [
                {
                    "type": h.hazard_type.value,
                    "description": h.description,
                    "location": h.location,
                    "severity": h.severity.value,
                    "worker_in_danger": h.worker_in_danger,
                }
                for h in classification.hazards
            ]

        return alert

    # ── helpers ──

    def _enforce_word_limit(self, text: str, severity: str) -> str:
        """Truncate audio text to max_audio_words for CRITICAL alerts."""
        if severity == "CRITICAL":
            words = text.split()
            if len(words) > self.max_audio_words:
                text = " ".join(words[: self.max_audio_words])
                logger.warning(
                    "Audio text truncated to %d words for CRITICAL alert.",
                    self.max_audio_words,
                )
        return text

    def _generate_audio_text(
        self,
        primary_hazard: Any,
        overall_severity: SeverityLevel,
    ) -> str:
        """Generate concise audio alert text from the primary hazard."""
        severity_prefix = {
            SeverityLevel.CRITICAL: "STOP!",
            SeverityLevel.WARNING: "Caution.",
            SeverityLevel.INFO: "Note:",
            SeverityLevel.NONE: "",
        }
        prefix = severity_prefix.get(overall_severity, "")
        desc = primary_hazard.description[:80]
        loc = primary_hazard.location

        text = f"{prefix} {desc}. Location: {loc}."

        # Enforce word limit
        words = text.split()
        if overall_severity == SeverityLevel.CRITICAL and len(words) > self.max_audio_words:
            text = " ".join(words[: self.max_audio_words])

        return text.strip()

    def _generate_hud_card(self, classification: ClassificationResult) -> str:
        """Generate bullet-point HUD display card."""
        lines = [f"⚠ {classification.overall_severity.value} ALERT"]
        for h in classification.hazards[:4]:  # Max 4 items on HUD
            icon = {
                HazardType.FALL_RISK: "🔻",
                HazardType.HEAVY_MACHINERY: "🏗",
                HazardType.ELECTRICAL: "⚡",
                HazardType.PPE_BREACH: "🦺",
                HazardType.STRUCTURAL: "🔧",
                HazardType.GENERAL: "⚠",
            }.get(h.hazard_type, "⚠")
            lines.append(f"{icon} {h.hazard_type.value}: {h.description[:60]}")
        return "\n".join(lines)

    def _generate_recommendation(
        self,
        primary: Any,
        classification: ClassificationResult,
    ) -> str:
        """Generate step-by-step mitigation based on hazard type."""
        recommendations = {
            HazardType.FALL_RISK: (
                "1. Stop work immediately.\n"
                "2. Move away from unprotected edge.\n"
                "3. Secure fall protection harness before continuing.\n"
                "4. Report to supervisor."
            ),
            HazardType.HEAVY_MACHINERY: (
                "1. Maintain safe distance from operating machinery.\n"
                "2. Ensure signal person is present.\n"
                "3. Verify load rigging before proceeding.\n"
                "4. Wear required high-visibility PPE."
            ),
            HazardType.ELECTRICAL: (
                "1. Do NOT touch any exposed wiring.\n"
                "2. Move at least 10 feet from the hazard.\n"
                "3. Call qualified electrician immediately.\n"
                "4. Report to supervisor for lockout/tagout."
            ),
            HazardType.PPE_BREACH: (
                "1. Stop work and put on required PPE.\n"
                "2. Check PPE condition and fit.\n"
                "3. Resume work only when fully compliant.\n"
                "4. Report missing PPE to site foreman."
            ),
            HazardType.STRUCTURAL: (
                "1. Evacuate the immediate area.\n"
                "2. Do not enter or load the affected structure.\n"
                "3. Alert structural engineer for assessment.\n"
                "4. Establish a safety perimeter."
            ),
            HazardType.GENERAL: (
                "1. Assess the situation carefully.\n"
                "2. Follow standard site safety procedures.\n"
                "3. Report any concerns to supervisor.\n"
                "4. Document the observation."
            ),
        }
        return recommendations.get(primary.hazard_type, recommendations[HazardType.GENERAL])
