from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import get_db
from services.report_service import build_report, serialize_report

router = APIRouter(tags=["Reports & Insights"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.get("/api/sessions/{session_id}/reports/latest", response_model=models.SiteReportResponse | None)
def latest_report(session_id: str, db: Session = Depends(get_db)) -> models.SiteReportResponse | None:
    report = db.scalars(
        select(models.SiteReportModel)
        .where(models.SiteReportModel.session_id == session_id, models.SiteReportModel.is_latest.is_(True))
        .order_by(models.SiteReportModel.created_at.desc())
    ).first()
    return serialize_report(report) if report else None


@router.post("/api/sessions/{session_id}/reports/generate", response_model=models.SiteReportResponse, status_code=201)
def generate_report(session_id: str, db: Session = Depends(get_db)) -> models.SiteReportResponse:
    session = db.get(models.SiteSessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    event = db.scalars(
        select(models.GlassesEventModel)
        .where(models.GlassesEventModel.session_id == session_id)
        .order_by(models.GlassesEventModel.created_at.desc())
    ).first()

    session.updated_at = now_utc()
    report = build_report(session, event, db)
    return serialize_report(report)


@router.get("/api/reports", response_model=list[models.SiteReportResponse])
@router.get("/api/web/reports", response_model=list[models.SiteReportResponse], include_in_schema=False)
def list_reports(db: Session = Depends(get_db)) -> list[models.SiteReportResponse]:
    reports = db.scalars(select(models.SiteReportModel).order_by(models.SiteReportModel.created_at.desc())).all()
    return [serialize_report(report) for report in reports]
