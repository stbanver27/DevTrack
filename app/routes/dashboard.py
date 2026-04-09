from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.models.project import Project
from app.models.activity import ActivityLog
from app.utils.deps import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    total_tasks = db.query(Task).count()
    done_tasks = db.query(Task).filter(Task.status == TaskStatus.done).count()
    in_progress = db.query(Task).filter(Task.status == TaskStatus.in_progress).count()
    pending = total_tasks - done_tasks

    projects = db.query(Project).filter(Project.is_archived == False).all()
    project_stats = []
    for p in projects:
        total = len(p.tasks)
        done = sum(1 for t in p.tasks if t.status == TaskStatus.done)
        project_stats.append({
            "id": p.id,
            "name": p.name,
            "color": p.color,
            "total": total,
            "done": done,
            "percent": int((done / total) * 100) if total > 0 else 0,
        })

    recent_activity = (
        db.query(ActivityLog)
        .order_by(ActivityLog.created_at.desc())
        .limit(15)
        .all()
    )

    return templates.TemplateResponse("dashboard/index.html", {
        "request": request,
        "user": user,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "in_progress": in_progress,
        "pending": pending,
        "project_stats": project_stats,
        "recent_activity": recent_activity,
        "active_page": "dashboard",
    })
