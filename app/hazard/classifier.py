"""
SiteLens AI — Hazard Classification Matrix

Maps VLM visual analysis output to deterministic severity levels
following the CRITICAL / WARNING / INFO / NONE matrix from the
system architecture.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("sitelens.hazard.classifier")


# ── Enums ────────────────────────────────────────────────────────────────

class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    NONE = "NONE"


class HazardType(str, Enum):
    FALL_RISK = "Fall Risk"
    HEAVY_MACHINERY = "Heavy Machinery"
    ELECTRICAL = "Electrical"
    PPE_BREACH = "PPE Breach"
    STRUCTURAL = "Structural"
    GENERAL = "General"


# ── Data classes ─────────────────────────────────────────────────────────

@dataclass
class DetectedHazard:
    """A single hazard extracted from VLM analysis."""
    hazard_type: HazardType
    description: str
    location: str
    severity: SeverityLevel
    worker_in_danger: bool


@dataclass
class ClassificationResult:
    """Aggregated classification from all detected hazards."""
    hazards: list[DetectedHazard] = field(default_factory=list)
    overall_severity: SeverityLevel = SeverityLevel.NONE
    scene_description: str = ""
    worker_count: int = 0
    ppe_compliance: str = ""
    escalate: bool = False


# ── Keyword → severity mappings ──────────────────────────────────────────

CRITICAL_KEYWORDS = {
    "crane", "overhead load", "swinging", "unharnessed", "unharness",
    "no harness", "above 6", "high-voltage", "high voltage", "exposed wiring",
    "trench collapse", "cave-in", "electrocution", "falling", "suspended load",
    "collapse", "structural failure", "live wire", "power line",
    "no fall protection", "open edge", "unguarded hole",
}

WARNING_KEYWORDS = {
    "missing", "no hard hat", "no helmet", "no safety glasses",
    "no gloves", "no hi-vis", "blocked exit", "improper storage",
    "housekeeping", "tripping", "wet floor", "fire extinguisher",
    "unsecured", "ppe", "violation",
    # PPE-specific absence phrases
    "without hard hat", "without helmet", "without vest", "without gloves",
    "without safety glasses", "without ppe", "bareheaded", "no vest",
    "no boots", "not wearing", "lacking ppe", "inadequate ppe",
    "non-compliant", "no protective", "unprotected worker",
}


# ── Classifier ───────────────────────────────────────────────────────────

class HazardClassifier:
    """
    Deterministic classifier that normalizes VLM JSON output into
    structured ``ClassificationResult`` with severity escalation.
    """

    @staticmethod
    def _map_hazard_type(raw_type: str) -> HazardType:
        """Fuzzy-match a raw hazard type string to our enum."""
        raw = raw_type.lower()
        if "fall" in raw:
            return HazardType.FALL_RISK
        if "machiner" in raw or "crane" in raw or "vehicle" in raw:
            return HazardType.HEAVY_MACHINERY
        if "electr" in raw or "wiring" in raw or "voltage" in raw:
            return HazardType.ELECTRICAL
        if "ppe" in raw or "protect" in raw or "equip" in raw:
            return HazardType.PPE_BREACH
        if "struct" in raw or "trench" in raw or "collapse" in raw:
            return HazardType.STRUCTURAL
        return HazardType.GENERAL

    @staticmethod
    def _map_severity(raw_severity: str, description: str = "") -> SeverityLevel:
        """Map raw severity string, with keyword-based override."""
        desc_lower = description.lower()

        # Keyword override — promote to CRITICAL if life-risk keywords
        for kw in CRITICAL_KEYWORDS:
            if kw in desc_lower:
                return SeverityLevel.CRITICAL

        raw = raw_severity.upper().strip()
        if raw == "CRITICAL":
            return SeverityLevel.CRITICAL
        if raw == "WARNING":
            # Check if it should be upgraded
            for kw in CRITICAL_KEYWORDS:
                if kw in desc_lower:
                    return SeverityLevel.CRITICAL
            return SeverityLevel.WARNING
        if raw == "INFO":
            return SeverityLevel.INFO
        return SeverityLevel.INFO

    def classify(self, vlm_output: dict[str, Any]) -> ClassificationResult:
        """
        Take the raw VLM JSON and produce a structured ClassificationResult.

        Parameters
        ----------
        vlm_output : dict from VLMEngine.analyze_frame()

        Returns
        -------
        ClassificationResult
        """
        result = ClassificationResult(
            scene_description=vlm_output.get("scene_description", ""),
            worker_count=vlm_output.get("worker_count", 0),
            ppe_compliance=vlm_output.get("ppe_compliance", ""),
        )

        raw_hazards = vlm_output.get("hazards_found", [])
        if not raw_hazards:
            # Even with no explicit hazards, check ppe_compliance for violations
            ppe_hazard = self._infer_ppe_hazard_from_compliance(
                result.ppe_compliance, result.worker_count
            )
            if ppe_hazard:
                result.hazards.append(ppe_hazard)
                result.overall_severity = SeverityLevel.WARNING
                logger.info("PPE hazard inferred from compliance text (no raw hazards)")
            else:
                result.overall_severity = SeverityLevel.NONE
            return result

        max_severity = SeverityLevel.NONE
        severity_order = {
            SeverityLevel.NONE: 0,
            SeverityLevel.INFO: 1,
            SeverityLevel.WARNING: 2,
            SeverityLevel.CRITICAL: 3,
        }

        for h in raw_hazards:
            hazard_type = self._map_hazard_type(h.get("type", "General"))
            severity = self._map_severity(
                h.get("severity", "INFO"),
                h.get("description", ""),
            )
            detected = DetectedHazard(
                hazard_type=hazard_type,
                description=h.get("description", "Unknown hazard"),
                location=h.get("location", "Unknown"),
                severity=severity,
                worker_in_danger=h.get("worker_in_danger", False),
            )
            result.hazards.append(detected)

            if severity_order.get(severity, 0) > severity_order.get(max_severity, 0):
                max_severity = severity

            # Any worker in immediate danger → force CRITICAL
            if detected.worker_in_danger:
                max_severity = SeverityLevel.CRITICAL

        result.overall_severity = max_severity
        result.escalate = max_severity == SeverityLevel.CRITICAL

        # ── Safety net: also check ppe_compliance for missed violations ──
        ppe_hazard = self._infer_ppe_hazard_from_compliance(result.ppe_compliance, result.worker_count)
        if ppe_hazard:
            # Only add if not already covered by an existing PPE hazard
            existing_ppe = any(h.hazard_type == HazardType.PPE_BREACH for h in result.hazards)
            if not existing_ppe:
                result.hazards.append(ppe_hazard)
                if max_severity == SeverityLevel.NONE:
                    result.overall_severity = SeverityLevel.WARNING

        logger.info(
            "Classification: %d hazards, overall=%s, escalate=%s",
            len(result.hazards),
            result.overall_severity.value,
            result.escalate,
        )
        return result

    def _infer_ppe_hazard_from_compliance(
        self,
        ppe_compliance: str,
        worker_count: int = 0,
    ) -> DetectedHazard | None:
        """
        Invert logic: assume PPE non-compliance UNLESS the VLM explicitly
        confirms every worker is wearing required gear.

        If a person is visible (worker_count > 0) and the ppe_compliance
        field does NOT contain an unambiguous confirmation of full compliance,
        a WARNING-level PPE Breach hazard is synthesised.
        """
        text = (ppe_compliance or "").lower().strip()

        # ── Step 1: Check for EXPLICIT compliance confirmations ──
        # These phrases mean the VLM is sure all PPE is worn correctly.
        # Use word-boundary-safe substring matching.
        COMPLIANT_PHRASES = [
            "all workers wearing",
            "wearing all required",
            "all required ppe",
            "full ppe compliance",
            "properly equipped",
            "full compliance",
            "all ppe present",
            "wearing hard hat and",
            "wearing hi-vis",
            "wearing safety vest",
            "no ppe violations",
            "all workers appear to be in compliance",
        ]
        for phrase in COMPLIANT_PHRASES:
            if phrase in text:
                logger.debug("PPE compliance confirmed via phrase: '%s'", phrase)
                return None

        # 'compliant' alone is positive ONLY if 'non-' does not precede it
        import re as _re
        if _re.search(r'(?<!non-)\bcompliant\b', text):
            return None

        # ── Step 2: If a person is visible — warn unless proven compliant ──
        if worker_count > 0:
            desc = ppe_compliance.strip() if ppe_compliance else "Worker(s) visible without confirmed PPE compliance"
            logger.info(
                "PPE WARNING: %d worker(s) visible, no explicit compliance confirmed. ppe_compliance='%s'",
                worker_count,
                ppe_compliance[:100] if ppe_compliance else "(empty)",
            )
            return DetectedHazard(
                hazard_type=HazardType.PPE_BREACH,
                description=desc,
                location="visible worker(s)",
                severity=SeverityLevel.WARNING,
                worker_in_danger=False,
            )

        # ── Step 3: Even without worker_count, check explicit violation phrases ──
        VIOLATION_PHRASES = [
            "not wearing", "missing", "no hard hat", "no helmet",
            "no vest", "no hi-vis", "no gloves", "no safety glasses",
            "without ppe", "without hard hat", "without helmet",
            "bareheaded", "non-compliant", "lacks", "lacking",
            "inadequate", "no protective", "unprotected", "no boots",
            "without gloves", "without vest", "violation",
            "no ppe", "no personal protective",
        ]
        triggered = [p for p in VIOLATION_PHRASES if p in text]
        if triggered:
            desc = ppe_compliance.strip().rstrip(".")
            logger.info(
                "PPE hazard via explicit violation phrase(s) %s in: '%s'",
                triggered[:3],
                ppe_compliance[:80],
            )
            return DetectedHazard(
                hazard_type=HazardType.PPE_BREACH,
                description=desc,
                location="visible worker(s)",
                severity=SeverityLevel.WARNING,
                worker_in_danger=False,
            )

        return None
