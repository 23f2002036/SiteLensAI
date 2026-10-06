from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import uuid4

import models
from database import get_db
from utils.auth_utils import validate_admin_creation_restriction

router = APIRouter(tags=["Authentication & Users"])


def format_user_response(user: models.UserModel) -> models.UserResponse:
    role_name = user.role_rel.role if user.role_rel else f"Role-{user.role_id}"
    full_name = user.username
    contact = None
    emergency_contact = None
    blood_type = None
    mail = None
    sub_role = None
    experience = None

    if user.admin_profile:
        full_name = user.admin_profile.name
        mail = user.admin_profile.admin_mail
        contact = user.admin_profile.admin_contact
    elif user.supervisor_profile:
        full_name = user.supervisor_profile.name
        mail = user.supervisor_profile.email
        contact = user.supervisor_profile.contact
        emergency_contact = user.supervisor_profile.emergency_contact
        experience = user.supervisor_profile.experience
    elif user.site_manager_profile:
        full_name = user.site_manager_profile.name
        mail = user.site_manager_profile.email
        contact = user.site_manager_profile.contact
        emergency_contact = user.site_manager_profile.emergency_contact
        blood_type = user.site_manager_profile.blood_group
    elif user.field_worker_profile:
        full_name = user.field_worker_profile.name
        mail = user.field_worker_profile.email
        contact = user.field_worker_profile.contact
        emergency_contact = user.field_worker_profile.emergency_contact
        blood_type = user.field_worker_profile.blood_group
        sub_role = user.field_worker_profile.sub_role

    return models.UserResponse(
        id=user.user_id,
        emp_id=user.emp_id,
        username=user.username,
        full_name=full_name,
        role=role_name,
        role_id=user.role_id,
        sub_role=sub_role,
        contact=contact,
        emergency_contact=emergency_contact,
        blood_type=blood_type,
        mail=mail,
        experience=experience,
    )


@router.post("/api/auth/login", response_model=models.UserResponse)
@router.post("/api/login", response_model=models.UserResponse, include_in_schema=False)
def login(payload: models.LoginRequest, db: Session = Depends(get_db)) -> models.UserResponse:
    user = db.scalars(
        select(models.UserModel).where(
            models.UserModel.username == payload.username,
            models.UserModel.password_hash == payload.password
        )
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return format_user_response(user)


@router.post("/api/users/create", response_model=models.UserResponse, status_code=201)
@router.post("/api/auth/users/create", response_model=models.UserResponse, status_code=201, include_in_schema=False)
def create_user(payload: models.UserCreateRequest, db: Session = Depends(get_db)) -> models.UserResponse:
    role = db.get(models.RoleModel, payload.role_id)
    role_name = role.role if role else "worker"
    validate_admin_creation_restriction(role_name, payload.sub_role, payload.username)

    existing = db.scalars(
        select(models.UserModel).where(models.UserModel.username == payload.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    emp_id = f"EMP-{uuid4().hex[:8].upper()}"
    new_user = models.UserModel(
        username=payload.username,
        password_hash=payload.password,
        emp_id=emp_id,
        role_id=payload.role_id,
    )
    db.add(new_user)
    db.flush()

    if payload.role_id == 1:
        profile = models.AdminModel(
            emp_id=new_user.emp_id,
            user_id=new_user.user_id,
            name=payload.full_name,
            admin_mail=payload.mail,
            admin_contact=payload.contact,
        )
        db.add(profile)
    elif payload.role_id == 2:
        profile = models.SupervisorModel(
            emp_id=new_user.emp_id,
            user_id=new_user.user_id,
            name=payload.full_name,
            email=payload.mail,
            contact=payload.contact,
            emergency_contact=payload.emergency_contact,
            experience=payload.experience,
        )
        db.add(profile)
    elif payload.role_id == 3:
        profile = models.SiteManagerModel(
            emp_id=new_user.emp_id,
            user_id=new_user.user_id,
            name=payload.full_name,
            email=payload.mail,
            contact=payload.contact,
            emergency_contact=payload.emergency_contact,
            blood_group=payload.blood_group,
        )
        db.add(profile)
    else:
        profile = models.FieldWorkerModel(
            emp_id=new_user.emp_id,
            user_id=new_user.user_id,
            name=payload.full_name,
            email=payload.mail,
            contact=payload.contact,
            emergency_contact=payload.emergency_contact,
            blood_group=payload.blood_group,
            sub_role=payload.sub_role,
        )
        db.add(profile)

    db.commit()
    db.refresh(new_user)

    return format_user_response(new_user)
