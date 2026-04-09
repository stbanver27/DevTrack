from sqlalchemy.orm import Session
from app.models.activity import ActivityLog


def log_activity(db: Session, user_id: int, action: str, detail: str = None, task_id: int = None):
    entry = ActivityLog(
        user_id=user_id,
        action=action,
        detail=detail,
        task_id=task_id,
    )
    db.add(entry)
    db.commit()
