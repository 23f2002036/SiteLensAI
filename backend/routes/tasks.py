from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
from database import get_db
from services.task_service import get_user_tasks

router = APIRouter(tags=["Tasks"])


@router.get("/api/tasks/{user_id}", response_model=list[models.TaskResponse])
def list_user_tasks(user_id: str, db: Session = Depends(get_db)) -> list[models.TaskResponse]:
    tasks = get_user_tasks(user_id, db)
    return [
        models.TaskResponse(
            id=t.task_id,
            site_id=t.site_id,
            assigned_by=t.assigned_by,
            assigned_to=t.assigned_to,
            due_date=t.due_date.isoformat() if t.due_date else None,
            status=t.status,
            task_name=t.task_name,
            task_description=t.task_description,
            created_at=t.created_at.isoformat() if t.created_at else None,
        ) for t in tasks
    ]
