from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from services.ai_service import classify_event


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def serialize_session(session: models.SiteSessionModel) -> models.SessionResponse:
    return models.SessionResponse(
        id=session.id,
        worker_name=session.worker_name,
        site_name=session.site_name,
        language=session.language,
        glasses_id=session.glasses_id,
        status=session.status,
        is_live=session.is_live,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


def serialize_event(event: models.GlassesEventModel) -> models.GlassesEventResponse:
    return models.GlassesEventResponse(
        id=event.id,
        session_id=event.session_id,
        event_type=event.event_type,
        source=event.source,
        camera_observation=event.camera_observation,
        audio_transcript=event.audio_transcript,
        hazard_flags=list(event.hazard_flags or []),
        metadata=dict(event.event_metadata or {}),
        created_at=event.created_at.isoformat(),
    )


def serialize_report(report: models.SiteReportModel) -> models.SiteReportResponse:
    return models.SiteReportResponse(
        id=report.id,
        session_id=report.session_id,
        title=report.title,
        summary=report.summary,
        severity=report.severity,
        recommended_actions=list(report.recommended_actions or []),
        metrics=dict(report.metrics or {}),
        attachments=list(report.attachments or []),
        reported_by=report.reported_by,
        reported_to=report.reported_to,
        is_latest=report.is_latest,
        created_at=report.created_at.isoformat(),
    )


def serialize_dashboard_summary(
    sessions: list[models.SiteSessionModel],
    events: list[models.GlassesEventModel],
    reports: list[models.SiteReportModel],
) -> models.DashboardSummaryResponse:
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for report in reports:
        severity_counts[report.severity.lower()] = severity_counts.get(report.severity.lower(), 0) + 1

    latest_report = reports[0] if reports else None
    recent_reports = reports[:6]

    return models.DashboardSummaryResponse(
        total_sessions=len(sessions),
        active_sessions=sum(1 for session in sessions if session.is_live),
        total_events=len(events),
        total_reports=len(reports),
        high_severity_reports=severity_counts.get("high", 0),
        medium_severity_reports=severity_counts.get("medium", 0),
        low_severity_reports=severity_counts.get("low", 0),
        latest_report=serialize_report(latest_report) if latest_report else None,
        recent_reports=[serialize_report(report) for report in recent_reports],
        last_updated=now_utc().isoformat(),
    )


def build_report(session: models.SiteSessionModel, event: models.GlassesEventModel | None, db: Session) -> models.SiteReportModel:
    events = db.scalars(
        select(models.GlassesEventModel)
        .where(models.GlassesEventModel.session_id == session.id)
        .order_by(models.GlassesEventModel.created_at.asc())
    ).all()

    event_count = len(events)
    all_recommendations: list[str] = []
    max_severity_rank = 0  # 0: low, 1: medium, 2: high
    severity_map = {"low": 0, "medium": 1, "high": 2}
    rank_to_severity = {0: "low", 1: "medium", 2: "high"}

    for ev in events:
        sev, recs, _ = classify_event(
            models.GlassesEventCreate(
                event_type=ev.event_type,  # type: ignore[arg-type]
                source=ev.source,
                camera_observation=ev.camera_observation,
                audio_transcript=ev.audio_transcript,
                hazard_flags=list(ev.hazard_flags or []),
                metadata=dict(ev.event_metadata or {}),
            ),
            language=session.language,
        )
        sev_rank = severity_map.get(sev.lower(), 0)
        if sev_rank > max_severity_rank:
            max_severity_rank = sev_rank

        for r in recs:
            if r not in all_recommendations:
                all_recommendations.append(r)

    overall_severity = rank_to_severity.get(max_severity_rank, "low")

    if all_recommendations:
        summary = (
            f"Session Summary for {session.worker_name} at {session.site_name}: "
            f"Analyzed {event_count} frame/audio events. "
            f"Identified Hazards & Guidance: {' | '.join(all_recommendations)}"
        )
    else:
        summary = "No hazards and recommendation found in your session."

    db.query(models.SiteReportModel).filter(models.SiteReportModel.session_id == session.id).update(
        {models.SiteReportModel.is_latest: False},
        synchronize_session=False,
    )
    report = models.SiteReportModel(
        session_id=session.id,
        title=f"Shift report for {session.worker_name}",
        summary=summary,
        severity=overall_severity,
        recommended_actions=all_recommendations,
        metrics={
            "event_count": event_count,
            "last_event_type": event.event_type if event else "summary",
            "language": session.language,
            "assistant_message": summary,
            "recommendation_count": len(all_recommendations),
        },
        reported_by=session.user_id,
        is_latest=True,
        created_at=now_utc(),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
