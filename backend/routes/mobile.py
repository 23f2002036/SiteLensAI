import os
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from database import SessionLocal, get_db
from services.ai_service import analyze_image_vlm, generate_ai_companion_response
from services.report_service import (
    build_report,
    serialize_event,
    serialize_report,
    serialize_session,
)


router = APIRouter(tags=["Mobile & Smart Glass"])


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/api/sessions/start", response_model=models.SessionResponse, status_code=201)
@router.post("/api/mobile/session/start", response_model=models.SessionResponse, status_code=201, include_in_schema=False)
def start_session(payload: models.SessionCreate, db: Session = Depends(get_db)) -> models.SessionResponse:
    session = models.SiteSessionModel(
        user_id=payload.user_id,
        worker_name=payload.worker_name,
        site_name=payload.site_name,
        language=payload.language,
        glasses_id=payload.glasses_id,
        status="active",
        is_live=True,
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return serialize_session(session)


@router.post("/api/sessions/{session_id}/stop", response_model=models.SessionResponse)
@router.post("/api/mobile/sessions/{session_id}/stop", response_model=models.SessionResponse, include_in_schema=False)
def stop_session(session_id: str, db: Session = Depends(get_db)) -> models.SessionResponse:
    session = db.get(models.SiteSessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_live = False
    session.status = "completed"
    session.updated_at = now_utc()
    db.commit()
    db.refresh(session)
    return serialize_session(session)


@router.get("/api/sessions/{session_id}", response_model=models.SessionResponse)
def get_session(session_id: str, db: Session = Depends(get_db)) -> models.SessionResponse:
    session = db.get(models.SiteSessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return serialize_session(session)


@router.post("/api/sessions/{session_id}/events", response_model=models.GlassesEventResponse, status_code=201)
def post_event(session_id: str, payload: models.GlassesEventCreate, db: Session = Depends(get_db)) -> models.GlassesEventResponse:
    session = db.get(models.SiteSessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    event = models.GlassesEventModel(
        session_id=session_id,
        event_type=payload.event_type,
        source=payload.source,
        camera_observation=payload.camera_observation,
        audio_transcript=payload.audio_transcript,
        hazard_flags=payload.hazard_flags,
        event_metadata=payload.metadata,
        created_at=now_utc(),
    )
    session.updated_at = now_utc()
    db.add(event)
    db.commit()
    db.refresh(event)
    return serialize_event(event)


@router.get("/api/sessions/{session_id}/events", response_model=list[models.GlassesEventResponse])
def list_events(session_id: str, db: Session = Depends(get_db)) -> list[models.GlassesEventResponse]:
    events = db.scalars(
        select(models.GlassesEventModel)
        .where(models.GlassesEventModel.session_id == session_id)
        .order_by(models.GlassesEventModel.created_at.asc())
    ).all()
    return [serialize_event(event) for event in events]


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in list(self.active_connections[session_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws/glasses/{session_id}")
async def glasses_socket(websocket: WebSocket, session_id: str) -> None:
    await manager.connect(session_id, websocket)
    db = SessionLocal()
    try:
        session = db.get(models.SiteSessionModel, session_id)
        if session is None:
            await websocket.send_json({"status": "error", "detail": "Session not found"})
            await websocket.close(code=1008)
            return

        await websocket.send_json(
            {
                "status": "connected",
                "session_id": session_id,
                "message": "SiteLens AI link established",
            }
        )
        while True:
            raw_payload = await websocket.receive_json()
            payload = models.GlassesSocketEvent.model_validate(raw_payload)
            event = models.GlassesEventModel(
                session_id=session_id,
                event_type=payload.event_type,
                source=payload.source,
                camera_observation=payload.camera_observation,
                audio_transcript=payload.audio_transcript,
                hazard_flags=payload.hazard_flags,
                event_metadata=payload.metadata,
                created_at=now_utc(),
            )
            session.updated_at = now_utc()
            db.add(event)
            db.commit()
            db.refresh(event)

            report = build_report(session, event, db)
            
            # Generate real-time AI Companion dialogue response
            is_voice_event = payload.event_type == "voice_note" or bool(payload.audio_transcript)
            is_manual_query = bool(payload.camera_observation) or payload.event_type in ["hazard_alert", "manual_note"]

            query_prompt = payload.audio_transcript or payload.camera_observation or "Analyze site status"
            analysis, severity, recommendations, assistant_msg = await generate_ai_companion_response(
                prompt=query_prompt, 
                image_url=payload.metadata.get("image_url", ""),
                language=session.language
            )

            # Suppress assistant_message for routine background frames unless a hazard is detected
            send_assistant_msg = assistant_msg
            if payload.event_type == "camera_frame" and not is_voice_event and not is_manual_query and severity == "low":
                send_assistant_msg = None

            ack = models.SocketAck(
                status="received",
                session_id=session_id,
                event=serialize_event(event),
                report=serialize_report(report),
                assistant_message=send_assistant_msg,
            )

            await websocket.send_json(ack.model_dump())
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"status": "error", "detail": str(exc)})
            await websocket.close(code=1003)
        except Exception:
            pass
    finally:
        manager.disconnect(session_id, websocket)
        db.close()


@router.post("/api/analyze", response_model=models.AnalyzeImageResponse, status_code=200)
@router.post("/analyze", response_model=models.AnalyzeImageResponse, status_code=200, include_in_schema=False)
async def analyze_frame(
    image: UploadFile = File(...),
    prompt: str = Form("Analyze this site frame for safety hazards"),
    language: str = Form("en"),
) -> models.AnalyzeImageResponse:
    contents = await image.read()

    os.makedirs("uploads/images", exist_ok=True)
    ext = os.path.splitext(image.filename or "frame.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join("uploads", "images", filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    image_url = f"/uploads/images/{filename}"
    analysis, severity, recommendations, assistant_msg = await generate_ai_companion_response(
        prompt=prompt, image_url=image_url, language=language
    )

    return models.AnalyzeImageResponse(
        status="success",
        filename=image.filename or filename,
        image_url=image_url,
        prompt=prompt,
        analysis=analysis,
        severity=severity,
        recommended_actions=recommendations,
    )


@router.post("/api/sessions/{session_id}/upload-frame", response_model=models.GlassesEventResponse, status_code=201)
async def upload_session_frame(
    session_id: str,
    image: UploadFile = File(...),
    prompt: str = Form("Analyze this site frame for safety hazards"),
    db: Session = Depends(get_db),
) -> models.GlassesEventResponse:
    session = db.get(models.SiteSessionModel, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    contents = await image.read()
    os.makedirs("uploads/images", exist_ok=True)
    ext = os.path.splitext(image.filename or "frame.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join("uploads", "images", filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    image_url = f"/uploads/images/{filename}"
    analysis, severity, recommendations, assistant_msg = await generate_ai_companion_response(
        prompt=prompt, image_url=image_url, language=session.language
    )

    # For background frame uploads, only broadcast assistant_message if a hazard is detected
    send_assistant_msg = assistant_msg if severity in ["high", "medium"] else None

    event = models.GlassesEventModel(
        session_id=session_id,
        event_type="camera_frame",
        source="phone-camera",
        camera_observation=f"Frame saved at {image_url}. {analysis}",
        audio_transcript=None,
        hazard_flags=recommendations if severity in ["high", "medium"] else [],
        event_metadata={
            "image_url": image_url,
            "filename": filename,
            "severity": severity,
            "recommendations": recommendations,
        },
        created_at=now_utc(),
    )
    session.updated_at = now_utc()
    db.add(event)
    db.commit()
    db.refresh(event)

    report = build_report(session, event, db)
    serialized_event = serialize_event(event)

    ack = models.SocketAck(
        status="received",
        session_id=session_id,
        event=serialized_event,
        report=serialize_report(report),
        assistant_message=send_assistant_msg,
    )
    
    # Broadcast to active WebSocket so mobile app receives AI voice response only when necessary
    await manager.broadcast(session_id, ack.model_dump())

    return serialized_event



