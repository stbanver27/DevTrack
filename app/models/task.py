from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base


class TaskStatus(str, enum.Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    paused = "paused"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Label(Base):
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), nullable=False, unique=True)
    color = Column(String(7), default="#6366f1")
    created_at = Column(DateTime, default=datetime.utcnow)

    task_labels = relationship("TaskLabel", back_populates="label", cascade="all, delete-orphan")


class TaskLabel(Base):
    __tablename__ = "task_labels"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    label_id = Column(Integer, ForeignKey("labels.id"), nullable=False)

    task = relationship("Task", back_populates="task_labels")
    label = relationship("Label", back_populates="task_labels")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.backlog, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    position = Column(Integer, default=0)  # for ordering within column
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="tasks")
    subtasks = relationship("SubTask", back_populates="task", cascade="all, delete-orphan")
    task_labels = relationship("TaskLabel", back_populates="task", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="task", cascade="all, delete-orphan")

    @property
    def labels(self):
        return [tl.label for tl in self.task_labels]

    @property
    def subtask_progress(self):
        total = len(self.subtasks)
        if total == 0:
            return None
        done = sum(1 for s in self.subtasks if s.is_done)
        return {"total": total, "done": done, "percent": int((done / total) * 100)}


class SubTask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    is_done = Column(Boolean, default=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="subtasks")
