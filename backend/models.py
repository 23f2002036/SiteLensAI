from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# --------------------------------------- DATA TABLES -------------------------------------------------------------

# 1. Role Table
class RoleModel(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    role: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    role_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    users: Mapped[list["UserModel"]] = relationship(back_populates="role_rel")


# 2. User Table (Authoritative location for Role & Auth)
class UserModel(Base):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    emp_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, default=lambda: f"EMP-{uuid4().hex[:8].upper()}")
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    role_rel: Mapped[RoleModel] = relationship(back_populates="users")
    admin_profile: Mapped["AdminModel | None"] = relationship(
        "AdminModel",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        primaryjoin="UserModel.user_id == AdminModel.user_id",
    )
    supervisor_profile: Mapped["SupervisorModel | None"] = relationship(
        "SupervisorModel",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        primaryjoin="UserModel.user_id == SupervisorModel.user_id",
    )
    site_manager_profile: Mapped["SiteManagerModel | None"] = relationship(
        "SiteManagerModel",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        primaryjoin="UserModel.user_id == SiteManagerModel.user_id",
    )
    field_worker_profile: Mapped["FieldWorkerModel | None"] = relationship(
        "FieldWorkerModel",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        primaryjoin="UserModel.user_id == FieldWorkerModel.user_id",
    )

    sessions: Mapped[list["SiteSessionModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")


# 3. Admin Table (Profile extension)
class AdminModel(Base):
    __tablename__ = "admin"

    emp_id: Mapped[str] = mapped_column(ForeignKey("users.emp_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    admin_mail: Mapped[str | None] = mapped_column(String(100), nullable=True)
    admin_contact: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="admin_profile",
        primaryjoin="AdminModel.user_id == UserModel.user_id",
    )


# 4. Supervisor Table (Profile extension)
class SupervisorModel(Base):
    __tablename__ = "supervisors"

    emp_id: Mapped[str] = mapped_column(ForeignKey("users.emp_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column("e-mail", String(100), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    experience: Mapped[str | None] = mapped_column(String(100), nullable=True)

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="supervisor_profile",
        primaryjoin="SupervisorModel.user_id == UserModel.user_id",
    )


# 5. Site Manager Table (Profile extension)
class SiteManagerModel(Base):
    __tablename__ = "site_managers"

    emp_id: Mapped[str] = mapped_column(ForeignKey("users.emp_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column("e-mail", String(100), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    blood_group: Mapped[str | None] = mapped_column("blood_group", String(10), nullable=True)

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="site_manager_profile",
        primaryjoin="SiteManagerModel.user_id == UserModel.user_id",
    )


# 6. Field Worker Table (Profile extension)
class FieldWorkerModel(Base):
    __tablename__ = "field_workers"

    emp_id: Mapped[str] = mapped_column(ForeignKey("users.emp_id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column("e-mail", String(100), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    blood_group: Mapped[str | None] = mapped_column("blood_group", String(10), nullable=True)
    sub_role: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped[UserModel] = relationship(
        "UserModel",
        back_populates="field_worker_profile",
        primaryjoin="FieldWorkerModel.user_id == UserModel.user_id",
    )


# 7. Site Table
class SiteModel(Base):
    __tablename__ = "sites"

    site_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    site_location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    site_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    site_manager: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    site_supervisor: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    no_of_employees: Mapped[int] = mapped_column("no.of_employees", Integer, nullable=False, default=0)
    no_of_glasses_used: Mapped[int] = mapped_column("no.of_glasses_used", Integer, nullable=False, default=0)


# 8. Task Table
class TaskModel(Base):
    __tablename__ = "tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=True)
    assigned_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    task_name: Mapped[str] = mapped_column("taskname", String(200), nullable=False)
    task_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


# 9. Unified Site Report Table
class SiteReportModel(Base):
    __tablename__ = "site_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("site_sessions.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Site Inspection Report")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, default="low")
    recommended_actions: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    attachments: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    reported_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    reported_to: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column("date&time", DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    session: Mapped["SiteSessionModel | None"] = relationship(back_populates="reports")

ReportModel = SiteReportModel


# 10. Glasses Table
class GlassesModel(Base):
    __tablename__ = "glasses"

    glasses_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.site_id", ondelete="CASCADE"), nullable=True)
    login_dt: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    logout_dt: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# ---------------------------------------------------------------------------------------------------------------------------
# Streaming Support Models for Smart Glass WebSocket & Live Dashboard
class SiteSessionModel(Base):
    __tablename__ = "site_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    worker_name: Mapped[str] = mapped_column(String(200), nullable=False)
    site_name: Mapped[str] = mapped_column(String(200), nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False, default="en")
    glasses_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    is_live: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped[UserModel | None] = relationship(back_populates="sessions")
    events: Mapped[list["GlassesEventModel"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    reports: Mapped[list["SiteReportModel"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class GlassesEventModel(Base):
    __tablename__ = "glasses_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("site_sessions.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="meta-glasses")
    camera_observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    hazard_flags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped[SiteSessionModel] = relationship(back_populates="events")

# ---------------------------------------------------------------------------------------------------------------------------
# Pydantic schemas for request and response validation

class SessionCreate(BaseModel):
    user_id: str | None = None
    worker_name: str = Field(min_length=1, max_length=200)
    site_name: str = Field(min_length=1, max_length=200)
    language: str = Field(default="en", min_length=2, max_length=32)
    glasses_id: str | None = Field(default=None, max_length=200)

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreateRequest(BaseModel):
    username: str
    password: str
    full_name: str
    role_id: int = Field(default=4, description="1: Super Admin, 2: Supervisor, 3: Site Manager, 4: Field Worker")
    sub_role: str | None = None
    contact: str | None = None
    emergency_contact: str | None = None
    blood_group: str | None = None
    mail: str | None = None
    experience: str | None = None

class UserResponse(BaseModel):
    id: str
    emp_id: str
    username: str
    full_name: str
    role: str
    role_id: int
    sub_role: str | None = None
    contact: str | None = None
    emergency_contact: str | None = None
    blood_type: str | None = None
    mail: str | None = None
    experience: str | None = None

class SiteResponse(BaseModel):
    id: int
    site_name: str | None = None
    site_location: str | None = None
    site_description: str | None = None
    client_name: str | None = None
    site_manager: str | None = None
    site_supervisor: str | None = None
    no_of_employees: int = 0
    no_of_glasses_used: int = 0

class TaskResponse(BaseModel):
    id: int
    site_id: int | None = None
    assigned_by: str | None = None
    assigned_to: str | None = None
    due_date: str | None = None
    status: str = "pending"
    task_name: str
    task_description: str | None = None
    created_at: str | None = None

class SessionResponse(BaseModel):
    id: str
    worker_name: str
    site_name: str
    language: str
    glasses_id: str | None
    status: str
    is_live: bool
    created_at: str
    updated_at: str

class GlassesEventCreate(BaseModel):
    event_type: Literal["camera_frame", "voice_note", "hazard_alert", "manual_note", "status_update"]
    source: str = Field(default="meta-glasses", max_length=64)
    camera_observation: str | None = Field(default=None)
    audio_transcript: str | None = Field(default=None)
    hazard_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class GlassesEventResponse(BaseModel):
    id: int
    session_id: str
    event_type: str
    source: str
    camera_observation: str | None
    audio_transcript: str | None
    hazard_flags: list[str]
    metadata: dict[str, Any]
    created_at: str

class SiteReportResponse(BaseModel):
    id: int
    session_id: str | None = None
    title: str
    summary: str
    severity: str
    recommended_actions: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)
    attachments: list[str] = Field(default_factory=list)
    reported_by: str | None = None
    reported_to: str | None = None
    is_latest: bool = True
    created_at: str

ReportResponse = SiteReportResponse

class DashboardSummaryResponse(BaseModel):
    total_sessions: int
    active_sessions: int
    total_events: int
    total_reports: int
    high_severity_reports: int
    medium_severity_reports: int
    low_severity_reports: int
    latest_report: SiteReportResponse | None
    recent_reports: list[SiteReportResponse]
    last_updated: str

class GlassesSocketEvent(BaseModel):
    event_type: str = Field(min_length=1, max_length=64)
    source: str = Field(default="meta-glasses", max_length=64)
    camera_observation: str | None = None
    audio_transcript: str | None = None
    hazard_flags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

class SocketAck(BaseModel):
    status: str
    session_id: str
    event: GlassesEventResponse | None = None
    report: SiteReportResponse | None = None
    assistant_message: str | None = None

class AnalyzeImageResponse(BaseModel):
    status: str
    filename: str
    image_url: str
    prompt: str
    analysis: str
    severity: str
    recommended_actions: list[str] = Field(default_factory=list)

