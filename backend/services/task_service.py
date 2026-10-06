from sqlalchemy import select, or_
from sqlalchemy.orm import Session

import models


def get_user_tasks(user_id: str, db: Session) -> list[models.TaskModel]:
    return db.scalars(
        select(models.TaskModel)
        .where(
            or_(
                models.TaskModel.assigned_to == user_id,
                models.TaskModel.assigned_by == user_id
            )
        )
        .order_by(models.TaskModel.created_at.desc())
    ).all()


def get_all_sites(db: Session) -> list[models.SiteModel]:
    return db.scalars(
        select(models.SiteModel).order_by(models.SiteModel.site_id.asc())
    ).all()
