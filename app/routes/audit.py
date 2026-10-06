"""
SiteLens AI — Audit Routes

Endpoints:
  GET  /api/audit/incidents        — List incidents with filters
  GET  /api/audit/incidents/{id}   — Get incident details
  GET  /api/audit/report           — Compliance summary report
  GET  /api/audit/export           — Export incidents as CSV
"""

from __future__ import annotations

import csv
import io
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger("sitelens.routes.audit")

router = APIRouter(prefix="/api/audit", tags=["audit"])

# ── Module-level singleton (injected via main.py lifespan) ──
_audit_db = None


def set_audit_db(db):
    global _audit_db
    _audit_db = db


@router.get("/incidents")
async def list_incidents(
    limit: int = Query(50, ge=1, le=500),
    severity: Optional[str] = Query(None, description="Filter by severity: CRITICAL, WARNING, INFO, NONE"),
    hazard_type: Optional[str] = Query(None, description="Filter by hazard type"),
):
    """List recent incidents with optional filters."""
    if _audit_db is None:
        raise HTTPException(status_code=503, detail="Audit database not initialized.")

    try:
        incidents = await _audit_db.get_incidents(
            limit=limit,
            severity=severity,
            hazard_type=hazard_type,
        )
        return {"count": len(incidents), "incidents": incidents}
    except Exception as e:
        logger.error("Failed to retrieve incidents: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Get details for a specific incident."""
    if _audit_db is None:
        raise HTTPException(status_code=503, detail="Audit database not initialized.")

    incident = await _audit_db.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")
    return incident


@router.get("/report")
async def compliance_report():
    """Generate a compliance summary report."""
    if _audit_db is None:
        raise HTTPException(status_code=503, detail="Audit database not initialized.")

    try:
        report = await _audit_db.get_compliance_report()
        return report
    except Exception as e:
        logger.error("Failed to generate report: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_csv(
    severity: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=5000),
):
    """Export incidents as CSV for audit trail."""
    if _audit_db is None:
        raise HTTPException(status_code=503, detail="Audit database not initialized.")

    incidents = await _audit_db.get_incidents(limit=limit, severity=severity)

    # Build CSV
    output = io.StringIO()
    if incidents:
        writer = csv.DictWriter(output, fieldnames=incidents[0].keys())
        writer.writeheader()
        writer.writerows(incidents)
    else:
        output.write("No incidents found.\n")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=sitelens_audit.csv"},
    )
