from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone
from app.db.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority, Label, TaskLabel
from app.models.project import Project
from app.models.activity import ActivityLog
from app.utils.deps import get_current_user
from app.services.activity_service import log_activity

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

COLUMNS = [
    ("backlog", "Backlog", "⬜"),
    ("todo", "To Do", "📋"),
    ("in_progress", "In Progress", "🔄"),
    ("paused", "Paused", "⏸️"),
    ("done", "Done", "✅"),
]


@router.get("/kanban", response_class=HTMLResponse)
def kanban_view(
    request: Request,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    projects = db.query(Project).filter(
        Project.owner_id == user.id, Project.is_archived == False
    ).all()

    task_query = db.query(Task)
    if project_id:
        task_query = task_query.filter(Task.project_id == project_id)
    else:
        project_ids = [p.id for p in projects]
        task_query = task_query.filter(Task.project_id.in_(project_ids))

    all_tasks = task_query.order_by(Task.position, Task.created_at).all()

    columns = {}
    for status, label, icon in COLUMNS:
        columns[status] = {
            "label": label,
            "icon": icon,
            "tasks": [t for t in all_tasks if t.status.value == status],
        }

    all_labels = db.query(Label).all()
    project_map = {p.id: p for p in projects}

    return templates.TemplateResponse("tasks/kanban.html", {
        "request": request,
        "user": user,
        "columns": columns,
        "projects": projects,
        "project_map": project_map,
        "selected_project_id": project_id,
        "all_labels": all_labels,
        "active_page": "kanban",
        "now": datetime.utcnow(),
    })


# ── Task CRUD API (JSON) ──────────────────────────────────────────────────────

@router.post("/api/tasks")
async def create_task(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.json()
    task = Task(
        title=data["title"],
        description=data.get("description", ""),
        status=TaskStatus(data.get("status", "backlog")),
        priority=TaskPriority(data.get("priority", "medium")),
        project_id=data["project_id"],
    )
    if data.get("due_date"):
        try:
            task.due_date = datetime.fromisoformat(data["due_date"])
        except Exception:
            pass

    db.add(task)
    db.flush()

    # Assign labels
    for label_id in data.get("label_ids", []):
        db.add(TaskLabel(task_id=task.id, label_id=label_id))

    db.commit()
    db.refresh(task)
    log_activity(db, user.id, "task_created", f"Tarea '{task.title}' creada", task.id)

    return _task_to_dict(task)


@router.put("/api/tasks/{task_id}")
async def update_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return JSONResponse({"error": "Not found"}, status_code=404)

    data = await request.json()
    old_status = task.status.value

    if "title" in data:
        task.title = data["title"]
    if "description" in data:
        task.description = data["description"]
    if "priority" in data:
        task.priority = TaskPriority(data["priority"])
    if "due_date" in data:
        task.due_date = datetime.fromisoformat(data["due_date"]) if data["due_date"] else None
    if "status" in data:
        new_status = data["status"]
        if new_status != old_status:
            task.status = TaskStatus(new_status)
            log_activity(db, user.id, "status_changed", f"{old_status} → {new_status}", task.id)
    if "position" in data:
        task.position = data["position"]
    if "label_ids" in data:
        db.query(TaskLabel).filter(TaskLabel.task_id == task.id).delete()
        for label_id in data["label_ids"]:
            db.add(TaskLabel(task_id=task.id, label_id=label_id))

    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return _task_to_dict(task)


@router.delete("/api/tasks/{task_id}")
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
        log_activity(db, user.id, "task_deleted", f"Tarea ID {task_id} eliminada")
    return JSONResponse({"ok": True})


@router.get("/api/tasks/{task_id}")
def get_task(task_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return JSONResponse({"error": "Not found"}, status_code=404)
    return _task_to_dict(task)


# ── SubTask API ───────────────────────────────────────────────────────────────

@router.post("/api/subtasks")
async def create_subtask(request: Request, db: Session = Depends(get_db)):
    from app.models.task import SubTask
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.json()
    subtask = SubTask(title=data["title"], task_id=data["task_id"])
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return {"id": subtask.id, "title": subtask.title, "is_done": subtask.is_done, "task_id": subtask.task_id}


@router.put("/api/subtasks/{subtask_id}")
async def update_subtask(subtask_id: int, request: Request, db: Session = Depends(get_db)):
    from app.models.task import SubTask
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    data = await request.json()
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id).first()
    if not subtask:
        return JSONResponse({"error": "Not found"}, status_code=404)

    if "is_done" in data:
        subtask.is_done = data["is_done"]
    if "title" in data:
        subtask.title = data["title"]
    db.commit()
    return {"id": subtask.id, "title": subtask.title, "is_done": subtask.is_done}


@router.delete("/api/subtasks/{subtask_id}")
def delete_subtask(subtask_id: int, request: Request, db: Session = Depends(get_db)):
    from app.models.task import SubTask
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    subtask = db.query(SubTask).filter(SubTask.id == subtask_id).first()
    if subtask:
        db.delete(subtask)
        db.commit()
    return JSONResponse({"ok": True})


# ── Labels API ────────────────────────────────────────────────────────────────

@router.get("/labels", response_class=HTMLResponse)
def labels_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    labels = db.query(Label).all()
    return templates.TemplateResponse("tasks/labels.html", {
        "request": request, "user": user, "labels": labels, "active_page": "labels"
    })


@router.post("/api/labels")
async def create_label(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    data = await request.json()
    label = Label(name=data["name"], color=data.get("color", "#6366f1"))
    db.add(label)
    db.commit()
    db.refresh(label)
    return {"id": label.id, "name": label.name, "color": label.color}


@router.delete("/api/labels/{label_id}")
def delete_label(label_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    label = db.query(Label).filter(Label.id == label_id).first()
    if label:
        db.delete(label)
        db.commit()
    return JSONResponse({"ok": True})


@router.get("/api/labels")
def api_labels(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    labels = db.query(Label).all()
    return [{"id": l.id, "name": l.name, "color": l.color} for l in labels]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _task_to_dict(task: Task) -> dict:
    progress = task.subtask_progress
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "project_id": task.project_id,
        "position": task.position,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "subtasks": [
            {"id": s.id, "title": s.title, "is_done": s.is_done}
            for s in task.subtasks
        ],
        "labels": [
            {"id": l.id, "name": l.name, "color": l.color}
            for l in task.labels
        ],
        "subtask_progress": progress,
    }
