from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.db.database import get_db
from app.models.project import Project
from app.models.task import TaskStatus
from app.utils.deps import get_current_user
from app.services.activity_service import log_activity

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _require_user(request: Request, db: Session):
    user = get_current_user(request, db)
    if not user:
        raise Exception("unauthenticated")
    return user


@router.get("/projects", response_class=HTMLResponse)
def projects_list(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    projects = db.query(Project).filter(Project.owner_id == user.id).order_by(Project.created_at.desc()).all()
    project_data = []
    for p in projects:
        total = len(p.tasks)
        done = sum(1 for t in p.tasks if t.status == TaskStatus.done)
        project_data.append({
            "id": p.id, "name": p.name, "description": p.description,
            "color": p.color, "is_archived": p.is_archived,
            "created_at": p.created_at, "total": total, "done": done,
            "percent": int((done / total) * 100) if total > 0 else 0,
        })

    return templates.TemplateResponse("projects/list.html", {
        "request": request, "user": user,
        "projects": project_data, "active_page": "projects",
    })


@router.post("/projects/create")
def create_project(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form("#6366f1"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    project = Project(name=name, description=description, color=color, owner_id=user.id)
    db.add(project)
    db.commit()
    log_activity(db, user.id, "project_created", f"Proyecto '{name}' creado")
    return RedirectResponse(url="/projects", status_code=302)


@router.post("/projects/{project_id}/edit")
def edit_project(
    project_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    color: str = Form("#6366f1"),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if project:
        project.name = name
        project.description = description
        project.color = color
        db.commit()
        log_activity(db, user.id, "project_updated", f"Proyecto '{name}' actualizado")
    return RedirectResponse(url="/projects", status_code=302)


@router.post("/projects/{project_id}/archive")
def archive_project(project_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if project:
        project.is_archived = not project.is_archived
        db.commit()
    return JSONResponse({"ok": True, "archived": project.is_archived if project else None})


@router.post("/projects/{project_id}/delete")
def delete_project(project_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if project:
        db.delete(project)
        db.commit()
    return RedirectResponse(url="/projects", status_code=302)


# ── API endpoints for JSON consumers ─────────────────────────────────────────

@router.get("/api/projects")
def api_projects(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    projects = db.query(Project).filter(Project.owner_id == user.id, Project.is_archived == False).all()
    return [{"id": p.id, "name": p.name, "color": p.color} for p in projects]
