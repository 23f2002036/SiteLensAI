import sys
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, Session

# Add current directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import models
from database import Base
from utils.config import DATABASE_URL


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def seed_database(db: Session) -> None:
    # 1. Seed Roles (Pre-defined)
    roles_data = [
        (1, "Super Admin", "Superior Authority"),
        (2, "Supervisor", "manages more than one site"),
        (3, "Site Manager", "Manages one particular site"),
        (4, "Field Worker", "One who works on one or more fields"),
    ]
    for role_id, role_name, desc in roles_data:
        existing_role = db.get(models.RoleModel, role_id)
        if not existing_role:
            db.add(models.RoleModel(role_id=role_id, role=role_name, role_description=desc))
    db.flush()
    print("[SiteLens AI] Seeded standard roles (1: Super Admin, 2: Supervisor, 3: Site Manager, 4: Field Worker).")

    # -----------------------------------------------------------------------------------------------------------

    # 2. Seed Admin User (Pre-defined)
    admin_user = db.scalars(
        select(models.UserModel).where(models.UserModel.username == "admin")
    ).first()

    if not admin_user:
        admin_user = models.UserModel(
            username="admin",
            password_hash="admin123",
            emp_id="EMP-ADMIN001",
            role_id=1,
        )
        db.add(admin_user)
        db.flush()

        admin_profile = models.AdminModel(
            emp_id=admin_user.emp_id,
            user_id=admin_user.user_id,
            name="SLen Admin",
            admin_mail="admin@sitelens.ai",
            admin_contact="044-2434223",
        )
        db.add(admin_profile)
        db.flush()
        print("[SiteLens AI] Created primary Admin account: username='admin'")
    else:
        print("[SiteLens AI] Admin account ('admin') already exists.")

    # -----------------------------------------------------------------------------------------------------------

    # 3. Seed Supervisor User
    sup_user = db.scalars(
        select(models.UserModel).where(models.UserModel.username == "supervisor1")
    ).first()
    if not sup_user:
        sup_user = models.UserModel(
            username="supervisor1",
            password_hash="super123",
            emp_id="EMP-SUP001",
            role_id=2,
        )
        db.add(sup_user)
        db.flush()

        sup_profile = models.SupervisorModel(
            emp_id=sup_user.emp_id,
            user_id=sup_user.user_id,
            name="Alex Rivera",
            email="alex@sitelens.ai",
            contact="9876543211",
            emergency_contact="7984561230",
            experience="7 years",
        )
        db.add(sup_profile)
        db.flush()
        print("[SiteLens AI] Created Supervisor dummy data: username='supervisor1'")

    # -----------------------------------------------------------------------------------------------------------

    # 4. Seed Site Manager User
    manager_user = db.scalars(
        select(models.UserModel).where(models.UserModel.username == "manager1")
    ).first()
    if not manager_user:
        manager_user = models.UserModel(
            username="manager1",
            password_hash="manager123",
            emp_id="EMP-MGR001",
            role_id=3,
        )
        db.add(manager_user)
        db.flush()

        mgr_profile = models.SiteManagerModel(
            emp_id=manager_user.emp_id,
            user_id=manager_user.user_id,
            name="Sarah Connor",
            email="sarah@sitelens.ai",
            contact="9876543210",
            emergency_contact="7984561239",
            blood_group="A+",
        )
        db.add(mgr_profile)
        db.flush()
        print("[SiteLens AI] Created Site Manager dummy data: username='manager1'")

    # -----------------------------------------------------------------------------------------------------------

    # 5. Seed Field Worker User
    worker_user = db.scalars(
        select(models.UserModel).where(models.UserModel.username == "worker1")
    ).first()
    if not worker_user:
        worker_user = models.UserModel(
            username="worker1",
            password_hash="worker123",
            emp_id="EMP-WRK001",
            role_id=4,
        )
        db.add(worker_user)
        db.flush()

        worker_profile = models.FieldWorkerModel(
            emp_id=worker_user.emp_id,
            user_id=worker_user.user_id,
            name="John Doe",
            email="john@sitelens.ai",
            contact="8654231797",
            emergency_contact="9875486287",
            blood_group="O-",
            sub_role="general labour",
        )
        db.add(worker_profile)
        db.flush()
        print("[SiteLens AI] Created Field Worker dummy data: username='worker1'")

    # -----------------------------------------------------------------------------------------------------------

    # 6. Default Sites
    existing_sites = db.scalars(select(models.SiteModel)).all()
    if not existing_sites:
        sites = [
            models.SiteModel(
                site_name="RM Flats",
                site_location="OMR, Chennai",
                site_description="Residential apartment complex under construction",
                client_name="RM Developers",
                site_manager=manager_user.user_id,
                site_supervisor=sup_user.user_id,
                no_of_employees=15,
                no_of_glasses_used=5,
            ),
            models.SiteModel(
                site_name="Prashant Towers",
                site_location="T Nagar, Chennai",
                site_description="Residential and commercial complex under construction",
                client_name="Prashant Group",
                site_manager=manager_user.user_id,
                site_supervisor=sup_user.user_id,
                no_of_employees=20,
                no_of_glasses_used=8,
            ),
            models.SiteModel(
                site_name="Arnav IT Park",
                site_location="Guindy, Chennai",
                site_description="IT infrastructure and office complex",
                client_name="Arnav Corp",
                site_manager=manager_user.user_id,
                site_supervisor=sup_user.user_id,
                no_of_employees=8,
                no_of_glasses_used=2,
            ),
        ]
        db.add_all(sites)
        db.flush()
        print("[SiteLens AI] Default construction sites seeded.")
    else:
        sites = existing_sites

    primary_site = sites[0]

    # -----------------------------------------------------------------------------------------------------------

    # 7. Default Tasks
    existing_tasks = db.scalars(select(models.TaskModel)).all()
    if not existing_tasks:
        tasks = [
            models.TaskModel(
                site_id=primary_site.site_id,
                assigned_by=manager_user.user_id,
                assigned_to=worker_user.user_id,
                task_name="Inspect North Tower Safety Equipment",
                task_description="Check helmets, harnesses, and fire extinguishers at Zone 3.",
                status="pending",
                created_at=now_utc(),
            ),
            models.TaskModel(
                site_id=primary_site.site_id,
                assigned_by=manager_user.user_id,
                assigned_to=worker_user.user_id,
                task_name="Verify Scaffolding Clamps at Level 5",
                task_description="Perform visual camera check of joint clamps.",
                status="pending",
                created_at=now_utc(),
            ),
            models.TaskModel(
                site_id=primary_site.site_id,
                assigned_by=manager_user.user_id,
                assigned_to=worker_user.user_id,
                task_name="Check Fire Extinguishers & First Aid Kit",
                task_description="Routine inspection of emergency gear.",
                status="completed",
                created_at=now_utc(),
            ),
        ]
        db.add_all(tasks)
        print("[SiteLens AI] Default tasks seeded.")

    # -----------------------------------------------------------------------------------------------------------

    # 8. Default Glasses Login Log
    existing_glasses = db.scalars(select(models.GlassesModel)).all()
    if not existing_glasses:
        glasses_log = models.GlassesModel(
            user_id=worker_user.user_id,
            site_id=primary_site.site_id,
            login_dt=now_utc(),
        )
        db.add(glasses_log)
        print("[SiteLens AI] Default glasses login log seeded.")

    # -----------------------------------------------------------------------------------------------------------

    # 9. Default Reports (Unified SiteReportModel)
    existing_reports = db.scalars(select(models.SiteReportModel)).all()
    if not existing_reports:
        sample_report = models.SiteReportModel(
            title="Initial Zone Safety Audit",
            summary="Routine zone safety audit completed. Harness compliance verified.",
            severity="low",
            recommended_actions=["Ensure hardhats worn in Zone B"],
            metrics={"event_count": 5},
            reported_by=worker_user.user_id,
            reported_to=manager_user.user_id,
            is_latest=True,
            created_at=now_utc(),
        )
        db.add(sample_report)
        print("[SiteLens AI] Default site report seeded.")

    db.commit()


def run_seed():
    print(f"[SiteLens AI Seed] Connecting to database: {DATABASE_URL}")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    print("[SiteLens AI Seed] Recreating database tables to match updated schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        print("[SiteLens AI Seed] Database successfully seeded!")

        users = db.scalars(select(models.UserModel)).all()
        print("\n--- Seeded Users ---")
        for u in users:
            role_title = u.role_rel.role if u.role_rel else f"Role #{u.role_id}"
            print(f"User ID: {u.user_id} | Emp ID: {u.emp_id} | Username: {u.username} | Role: {role_title}")

    except Exception as e:
        print(f"[SiteLens AI Seed] Error during database seeding: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
