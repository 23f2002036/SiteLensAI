"""
SiteLens AI — Ethical AI Safeguards

Privacy protocols, PII filtering, and content guardrails
to ensure the AI operates within harassment-free parameters.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("sitelens.safeguards")


# ── Privacy Directive (injected into VLM prompts) ────────────────────────

PRIVACY_DIRECTIVE = """
PRIVACY & ETHICS CONSTRAINTS (MANDATORY):
- Do NOT identify individuals by name, race, gender, age, ethnicity, or other personal characteristics.
- Refer to individuals ONLY by their role (e.g., "worker", "operator", "supervisor").
- Do NOT describe physical appearance beyond safety-relevant attributes (e.g., "worker without hard hat" is OK).
- Focus exclusively on safety hazards, compliance violations, and environmental risks.
- Do NOT make assumptions about worker competence, intent, or behavior beyond observable safety facts.
"""


class PrivacyFilter:
    """Strips personally identifiable information from VLM/LLM outputs."""

    # Patterns that might indicate PII in text
    PII_PATTERNS = [
        (r'\b[A-Z][a-z]+\s[A-Z][a-z]+\b', '[WORKER]'),  # Likely names (e.g., "John Smith")
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]'),  # Phone numbers
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),  # Emails
        (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),  # SSN
    ]

    # Identity descriptors to remove
    IDENTITY_TERMS = [
        r'\b(male|female|man|woman|boy|girl)\b',
        r'\b(caucasian|african|asian|hispanic|latino|latina|white|black|brown)\b',
        r'\b(old|young|elderly|aged|teen|teenage)\b',
    ]

    @classmethod
    def filter_text(cls, text: str) -> str:
        """Remove PII and identity descriptors from text."""
        filtered = text

        # Remove PII patterns
        for pattern, replacement in cls.PII_PATTERNS:
            filtered = re.sub(pattern, replacement, filtered)

        # Remove identity descriptors (case insensitive)
        for pattern in cls.IDENTITY_TERMS:
            filtered = re.sub(pattern, 'worker', filtered, flags=re.IGNORECASE)

        return filtered

    @classmethod
    def filter_alert(cls, alert_data: dict[str, Any]) -> dict[str, Any]:
        """Apply privacy filter to all text fields in an alert."""
        text_fields = [
            "audio_alert_text", "hud_display_card", "scene_description",
            "recommended_action", "sop_reference",
        ]
        for field in text_fields:
            if field in alert_data and isinstance(alert_data[field], str):
                alert_data[field] = cls.filter_text(alert_data[field])

        # Filter hazard details
        if "hazards_detail" in alert_data:
            for hazard in alert_data["hazards_detail"]:
                if "description" in hazard:
                    hazard["description"] = cls.filter_text(hazard["description"])

        return alert_data


class ContentGuard:
    """Validates LLM outputs for professional, safety-focused tone."""

    # Words/phrases that should never appear in safety alerts
    BLOCKED_TERMS = [
        r'\b(stupid|idiot|moron|incompetent|lazy|careless|negligent)\b',
        r'\b(blame|fault|guilty|responsible for)\b',
        r'\b(fired|terminated|punished|disciplined)\b',
    ]

    # Required professional tone indicators
    PROFESSIONAL_INDICATORS = [
        "hazard", "safety", "risk", "caution", "warning",
        "protection", "compliance", "procedure", "SOP",
    ]

    @classmethod
    def validate(cls, text: str) -> str:
        """
        Validate and clean LLM output for professional tone.
        Returns cleaned text.
        """
        cleaned = text

        # Remove blocked terms
        for pattern in cls.BLOCKED_TERMS:
            cleaned = re.sub(pattern, '[safety concern]', cleaned, flags=re.IGNORECASE)

        return cleaned

    @classmethod
    def validate_alert(cls, alert_data: dict[str, Any]) -> dict[str, Any]:
        """Apply content guard to all text fields in an alert."""
        text_fields = [
            "audio_alert_text", "hud_display_card",
            "recommended_action", "scene_description",
        ]
        for field in text_fields:
            if field in alert_data and isinstance(alert_data[field], str):
                alert_data[field] = cls.validate(alert_data[field])

        return alert_data


def apply_safeguards(alert_data: dict[str, Any]) -> dict[str, Any]:
    """Apply all ethical AI safeguards to an alert."""
    alert_data = PrivacyFilter.filter_alert(alert_data)
    alert_data = ContentGuard.validate_alert(alert_data)
    return alert_data
