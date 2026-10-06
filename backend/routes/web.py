from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import get_db
from services.report_service import serialize_dashboard_summary
from services.task_service import get_all_sites

router = APIRouter(tags=["Web Dashboard"])


@router.get("/api/dashboard/summary", response_model=models.DashboardSummaryResponse)
@router.get("/api/web/dashboard/summary", response_model=models.DashboardSummaryResponse, include_in_schema=False)
def dashboard_summary(db: Session = Depends(get_db)) -> models.DashboardSummaryResponse:
    sessions = db.scalars(select(models.SiteSessionModel).order_by(models.SiteSessionModel.updated_at.desc())).all()
    events = db.scalars(select(models.GlassesEventModel).order_by(models.GlassesEventModel.created_at.desc())).all()
    reports = db.scalars(select(models.SiteReportModel).order_by(models.SiteReportModel.created_at.desc())).all()
    return serialize_dashboard_summary(sessions, events, reports)


@router.get("/api/sites", response_model=list[models.SiteResponse])
@router.get("/api/web/sites", response_model=list[models.SiteResponse], include_in_schema=False)
def list_sites(db: Session = Depends(get_db)) -> list[models.SiteResponse]:
    sites = get_all_sites(db)
    return [
        models.SiteResponse(
            id=s.site_id,
            site_name=s.site_name,
            site_location=s.site_location,
            site_description=s.site_description,
            client_name=s.client_name,
            site_manager=s.site_manager,
            site_supervisor=s.site_supervisor,
            no_of_employees=s.no_of_employees,
            no_of_glasses_used=s.no_of_glasses_used,
        )
        for s in sites
    ]
