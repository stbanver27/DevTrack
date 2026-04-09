from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority


# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginForm(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── User ──────────────────────────────────────────────────────────────────────

class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Label ─────────────────────────────────────────────────────────────────────

class LabelCreate(BaseModel):
    name: str
    color: str = "#6366f1"


class LabelOut(BaseModel):
    id: int
    name: str
    color: str

    class Config:
        from_attributes = True


# ── Project ───────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "#6366f1"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_archived: Optional[bool] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    is_archived: bool
    created_at: datetime
    task_count: Optional[int] = 0
    done_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── SubTask ───────────────────────────────────────────────────────────────────

class SubTaskCreate(BaseModel):
    title: str
    task_id: int


class SubTaskUpdate(BaseModel):
    title: Optional[str] = None
    is_done: Optional[bool] = None


class SubTaskOut(BaseModel):
    id: int
    title: str
    is_done: bool
    task_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Task ──────────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.backlog
    priority: TaskPriority = TaskPriority.medium
    project_id: int
    due_date: Optional[datetime] = None
    label_ids: Optional[List[int]] = []


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    label_ids: Optional[List[int]] = None


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    project_id: int
    position: int
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    subtasks: List[SubTaskOut] = []
    labels: List[LabelOut] = []

    class Config:
        from_attributes = True


# ── Activity ──────────────────────────────────────────────────────────────────

class ActivityOut(BaseModel):
    id: int
    action: str
    detail: Optional[str]
    created_at: datetime
    task_id: Optional[int]

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_tasks: int
    done_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    total_projects: int
    recent_activity: List[ActivityOut] = []
