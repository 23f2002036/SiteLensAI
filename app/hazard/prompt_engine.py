"""
SiteLens AI — Prompt Engine

Builds the system prompt that combines VLM visual scene analysis with
retrieved RAG context to produce deterministic, real-time hazard alerts.

This is the core "brain" described in Section 3 of the architecture doc.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.config import get_settings

logger = logging.getLogger("sitelens.hazard.prompt")


# ── System prompt template ───────────────────────────────────────────────

SYSTEM_PROMPT_TEMPLATE = """SYSTEM PROMPT: Construction Site Hazard & SOP Verification System

[ROLE & CONTEXT]
You are SiteLens AI, an expert real-time safety engineer and physical AI assistant deployed
on smart glasses for construction site workers. Your primary function is life safety,
risk mitigation, and strict compliance enforcement.

[INPUT DATA]
1. Visual Analysis (from VLM): {vlm_scene_analysis}
2. Edge Alerts (from YOLO): {edge_detections}
3. Retrieved Standard Operating Procedures (RAG Context): {rag_retrieved_sops}
4. Worker Audio Query / Transcript: {worker_audio_input}

[HAZARD CLASSIFICATION MATRIX]
- SEVERITY CRITICAL: Immediate risk to life (e.g., active crane load swinging overhead,
  unharnessed work above 6ft, exposed high-voltage wiring, trench collapse risk).
- SEVERITY WARNING: Non-life-threatening safety breach (e.g., missing safety glasses,
  improper material storage, blocked emergency exits).
- SEVERITY INFO: Operational guidance or routine SOP verification.

[OPERATIONAL CONSTRAINTS]
1. BARS ON VERBOSITY: Audio output MUST be strictly under {max_audio_words} words for critical alerts.
2. DETERMINISTIC BEHAVIOR: Output valid JSON containing structured fields for audio
   synthesis, heads-up display (HUD), and manager logs.
3. NO HALLUCINATIONS: Base safety directives strictly on the provided RAG Context. If no
   SOP exists, cite standard fallback safety principles.

[OUTPUT FORMAT (STRICT JSON)]
You MUST respond with ONLY valid JSON in exactly this format, no other text:
{{
  "hazard_detected": true | false,
  "severity_level": "CRITICAL" | "WARNING" | "INFO" | "NONE",
  "hazard_type": "Fall Risk | Heavy Machinery | Electrical | PPE Breach | Structural | General",
  "audio_alert_text": "Short, clear text spoken directly to worker via smart glasses",
  "hud_display_card": "Key bullet points for AR display",
  "sop_reference": "Section or title of retrieved safety document used",
  "escalate_to_supervisor": true | false,
  "recommended_action": "Specific step-by-step mitigation instructions"
}}"""


# ── Builder ──────────────────────────────────────────────────────────────

class PromptEngine:
    """Builds structured prompts for the VLM/LLM to generate hazard alerts."""

    def __init__(self):
        self.settings = get_settings()

    def build_hazard_prompt(
        self,
        vlm_scene_analysis: dict[str, Any],
        edge_detections: Optional[dict[str, Any]] = None,
        rag_retrieved_sops: Optional[list[str]] = None,
        worker_audio_input: Optional[str] = None,
    ) -> str:
        """
        Assemble the full system prompt with all context injected.

        Parameters
        ----------
        vlm_scene_analysis : Parsed JSON from VLMEngine.analyze_frame()
        edge_detections    : YOLO bounding box detections (or None)
        rag_retrieved_sops : List of relevant SOP text chunks from RAG
        worker_audio_input : Transcribed worker voice query

        Returns
        -------
        Fully rendered system prompt string.
        """
        # Serialize inputs to clean text for injection
        vlm_text = json.dumps(vlm_scene_analysis, indent=2)

        edge_text = "No edge detection data available."
        if edge_detections:
            edge_text = json.dumps(edge_detections, indent=2)

        sop_text = "No SOPs retrieved. Use standard safety fallback principles."
        if rag_retrieved_sops:
            sop_text = "\n---\n".join(rag_retrieved_sops)

        audio_text = "No worker query."
        if worker_audio_input:
            audio_text = worker_audio_input

        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            vlm_scene_analysis=vlm_text,
            edge_detections=edge_text,
            rag_retrieved_sops=sop_text,
            worker_audio_input=audio_text,
            max_audio_words=self.settings.critical_audio_max_words,
        )

        logger.debug("Built hazard prompt (%d chars)", len(prompt))
        return prompt

    def build_vlm_prompt(
        self,
        worker_query: Optional[str] = None,
    ) -> str:
        """
        Build the VLM analysis prompt, optionally extended with the worker's query.

        If a worker_query is provided, it is appended as an additional focus
        instruction so the VLM tailors its scene analysis to the worker's concern
        while still returning the standard structured JSON.

        Parameters
        ----------
        worker_query : Optional free-text question or concern from the worker.

        Returns
        -------
        Prompt string to pass to VLMEngine.analyze_frame().
        """
        from app.models.vlm_engine import CONSTRUCTION_ANALYSIS_PROMPT

        if not worker_query:
            return CONSTRUCTION_ANALYSIS_PROMPT

        extended = (
            f"{CONSTRUCTION_ANALYSIS_PROMPT}\n\n"
            f"[WORKER QUERY — pay special attention to this]\n"
            f"{worker_query.strip()}\n\n"
            f"Make sure your JSON response specifically addresses the worker's query "
            f"in the 'scene_description' and any relevant hazard entries."
        )
        logger.debug("Built extended VLM prompt with worker query (%d chars)", len(extended))
        return extended

    def build_rag_query(
        self,
        vlm_scene_analysis: dict[str, Any],
        worker_audio_input: Optional[str] = None,
    ) -> str:
        """
        Build a semantic search query for the RAG vector store
        based on the VLM analysis and optional worker audio.

        Returns a natural-language query string optimized for
        embedding-based similarity search.
        """
        parts = []

        # Extract hazard descriptions from VLM output
        hazards = vlm_scene_analysis.get("hazards_found", [])
        if hazards:
            hazard_types = set()
            for h in hazards:
                hazard_types.add(h.get("type", ""))
                parts.append(h.get("description", ""))
            parts.insert(0, f"Construction safety SOP for: {', '.join(hazard_types)}")

        # Include worker query
        if worker_audio_input:
            parts.append(f"Worker question: {worker_audio_input}")

        # Fallback
        if not parts:
            scene = vlm_scene_analysis.get("scene_description", "construction site")
            parts.append(f"General safety procedures for: {scene}")

        query = " | ".join(parts)
        logger.debug("RAG query: %s", query[:200])
        return query
