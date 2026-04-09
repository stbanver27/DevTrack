"""
seed.py – Inicializa la base de datos con usuario admin y datos de prueba.
Ejecutar: python seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, init_db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task, SubTask, Label, TaskLabel, TaskStatus, TaskPriority
from app.models.activity import ActivityLog
from app.core.security import hash_password
from app.core.config import settings


def seed():
    init_db()
    db = SessionLocal()

    try:
        # ── Idempotency: skip if admin already exists ───────────────
        if db.query(User).filter(User.email == settings.ADMIN_EMAIL).first():
            print("✓ Seed ya ejecutado anteriormente. Base de datos no modificada.")
            return

        print("🌱 Inicializando base de datos...")

        # ── Admin user ──────────────────────────────────────────────
        admin = User(
            email=settings.ADMIN_EMAIL,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            full_name="Admin DevTrack",
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.flush()

        # ── Labels ──────────────────────────────────────────────────
        label_defs = [
            ("bug", "#ef4444"),
            ("feature", "#6366f1"),
            ("mejora", "#10b981"),
            ("docs", "#06b6d4"),
            ("urgente", "#f97316"),
            ("backend", "#8b5cf6"),
            ("frontend", "#ec4899"),
        ]
        labels = {}
        for name, color in label_defs:
            l = Label(name=name, color=color)
            db.add(l)
            db.flush()
            labels[name] = l

        # ── Projects ─────────────────────────────────────────────────
        p1 = Project(name="DevTrack v2", description="Siguiente versión con soporte multiusuario y SaaS.", color="#6366f1", owner_id=admin.id)
        p2 = Project(name="Portfolio Web", description="Sitio personal para mostrar proyectos y experiencia.", color="#10b981", owner_id=admin.id)
        p3 = Project(name="API REST Clientes", description="API para gestión de clientes de una empresa.", color="#f59e0b", owner_id=admin.id)

        db.add_all([p1, p2, p3])
        db.flush()

        # ── Tasks for p1 ─────────────────────────────────────────────
        tasks_p1 = [
            Task(title="Diseñar arquitectura multitenancy", description="Definir estrategia de aislamiento por tenant (schema vs row-level).", status=TaskStatus.done, priority=TaskPriority.critical, project_id=p1.id, position=1),
            Task(title="Implementar sistema de billing", description="Integrar Stripe con planes Free/Pro/Team.", status=TaskStatus.in_progress, priority=TaskPriority.high, project_id=p1.id, position=2),
            Task(title="Dashboard de métricas por workspace", status=TaskStatus.todo, priority=TaskPriority.medium, project_id=p1.id, position=3),
            Task(title="Módulo de invitaciones por email", status=TaskStatus.todo, priority=TaskPriority.medium, project_id=p1.id, position=4),
            Task(title="Tests de integración para auth", status=TaskStatus.backlog, priority=TaskPriority.low, project_id=p1.id, position=5),
            Task(title="Migrar a PostgreSQL en producción", status=TaskStatus.backlog, priority=TaskPriority.high, project_id=p1.id, position=6),
        ]

        # ── Tasks for p2 ─────────────────────────────────────────────
        tasks_p2 = [
            Task(title="Diseñar landing page personal", status=TaskStatus.done, priority=TaskPriority.high, project_id=p2.id, position=1),
            Task(title="Sección de proyectos con filtros", status=TaskStatus.in_progress, priority=TaskPriority.medium, project_id=p2.id, position=2),
            Task(title="Integrar blog con MDX", status=TaskStatus.todo, priority=TaskPriority.low, project_id=p2.id, position=3),
            Task(title="Optimizar SEO y meta tags", status=TaskStatus.backlog, priority=TaskPriority.medium, project_id=p2.id, position=4),
            Task(title="Deploy en Vercel + dominio", status=TaskStatus.paused, priority=TaskPriority.high, project_id=p2.id, position=5),
        ]

        # ── Tasks for p3 ─────────────────────────────────────────────
        tasks_p3 = [
            Task(title="CRUD de clientes con paginación", status=TaskStatus.done, priority=TaskPriority.high, project_id=p3.id, position=1),
            Task(title="Endpoint de reportes por período", status=TaskStatus.in_progress, priority=TaskPriority.medium, project_id=p3.id, position=2),
            Task(title="Autenticación OAuth2 + roles", status=TaskStatus.todo, priority=TaskPriority.critical, project_id=p3.id, position=3),
            Task(title="Rate limiting y throttling", status=TaskStatus.backlog, priority=TaskPriority.medium, project_id=p3.id, position=4),
        ]

        all_tasks = tasks_p1 + tasks_p2 + tasks_p3
        for t in all_tasks:
            db.add(t)
        db.flush()

        # ── Assign labels ─────────────────────────────────────────────
        label_assignments = [
            (tasks_p1[0], ["feature", "backend"]),
            (tasks_p1[1], ["feature", "urgente"]),
            (tasks_p1[2], ["feature", "frontend"]),
            (tasks_p2[0], ["frontend", "mejora"]),
            (tasks_p2[1], ["frontend", "feature"]),
            (tasks_p3[0], ["backend", "bug"]),
            (tasks_p3[2], ["backend", "urgente"]),
        ]
        for task, label_names in label_assignments:
            for name in label_names:
                db.add(TaskLabel(task_id=task.id, label_id=labels[name].id))

        # ── Subtasks ─────────────────────────────────────────────────
        subtasks_data = [
            (tasks_p1[1], [
                ("Crear cuenta Stripe Test", True),
                ("Webhook de eventos de pago", True),
                ("Tabla subscriptions en DB", False),
                ("Portal de gestión del cliente", False),
            ]),
            (tasks_p2[1], [
                ("Grid de proyectos responsive", True),
                ("Filtro por tecnología", False),
                ("Modal de detalle de proyecto", False),
            ]),
            (tasks_p3[1], [
                ("Query con filtros de fecha", True),
                ("Exportar a CSV", False),
                ("Gráfico de barras con Chart.js", False),
            ]),
        ]
        for task, subs in subtasks_data:
            for title, done in subs:
                db.add(SubTask(title=title, is_done=done, task_id=task.id))

        # ── Activity logs ─────────────────────────────────────────────
        activity_entries = [
            (admin.id, "project_created", "Proyecto 'DevTrack v2' creado", None),
            (admin.id, "project_created", "Proyecto 'Portfolio Web' creado", None),
            (admin.id, "project_created", "Proyecto 'API REST Clientes' creado", None),
            (admin.id, "task_created", "Tarea 'Diseñar arquitectura multitenancy' creada", tasks_p1[0].id),
            (admin.id, "status_changed", "backlog → done", tasks_p1[0].id),
            (admin.id, "task_created", "Tarea 'Implementar sistema de billing' creada", tasks_p1[1].id),
            (admin.id, "status_changed", "todo → in_progress", tasks_p1[1].id),
            (admin.id, "task_created", "Tarea 'CRUD de clientes con paginación' creada", tasks_p3[0].id),
            (admin.id, "status_changed", "in_progress → done", tasks_p3[0].id),
        ]
        for user_id, action, detail, task_id in activity_entries:
            db.add(ActivityLog(user_id=user_id, action=action, detail=detail, task_id=task_id))

        db.commit()

        print("✅ Seed completado exitosamente.")
        print()
        print("═" * 50)
        print("  CREDENCIALES DE ACCESO")
        print("═" * 50)
        print(f"  Email    : {settings.ADMIN_EMAIL}")
        print(f"  Password : {settings.ADMIN_PASSWORD}")
        print(f"  URL      : http://127.0.0.1:8000/login")
        print("═" * 50)
        print()
        print("  Datos de prueba creados:")
        print(f"  → 3 proyectos")
        print(f"  → {len(all_tasks)} tareas")
        print(f"  → 7 labels")
        print(f"  → Subtareas y logs de actividad")

    except Exception as e:
        db.rollback()
        print(f"❌ Error en seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
