# DevTrack

Sistema Kanban personal tipo mini-Jira, construido con **FastAPI + SQLAlchemy + SQLite + Jinja2**.  
Diseñado con arquitectura profesional lista para escalar a SaaS.

---

## Stack

| Capa       | Tecnología                          |
|------------|-------------------------------------|
| Backend    | FastAPI, SQLAlchemy, Pydantic       |
| Base datos | SQLite (producción → PostgreSQL)    |
| Auth       | JWT + bcrypt (passlib)              |
| Frontend   | Jinja2, HTML5, CSS Variables, JS    |
| Fonts      | Space Grotesk + JetBrains Mono      |

---

## Estructura

```
devtrack/
├── app/
│   ├── main.py                  # Punto de entrada FastAPI
│   ├── core/
│   │   ├── config.py            # Configuración global
│   │   └── security.py          # JWT, bcrypt, dependencias auth
│   ├── db/
│   │   └── database.py          # Conexión SQLite, Base, get_db
│   ├── models/
│   │   ├── user.py              # User
│   │   ├── project.py           # Project
│   │   ├── task.py              # Task, SubTask, Label, TaskLabel
│   │   └── activity.py          # ActivityLog
│   ├── schemas/
│   │   └── schemas.py           # Pydantic schemas
│   ├── routes/
│   │   ├── auth.py              # /login, /logout
│   │   ├── dashboard.py         # / (dashboard)
│   │   ├── projects.py          # /projects + /api/projects
│   │   └── tasks.py             # /kanban, /labels + API REST completa
│   ├── services/
│   │   └── activity_service.py  # log_activity()
│   ├── utils/
│   │   └── deps.py              # get_current_user, RequireAuth
│   ├── templates/
│   │   ├── partials/base.html   # Layout principal (sidebar + topbar)
│   │   ├── auth/login.html
│   │   ├── dashboard/index.html
│   │   ├── projects/list.html
│   │   └── tasks/
│   │       ├── kanban.html      # Tablero Kanban con D&D
│   │       └── labels.html
│   └── static/
│       ├── css/main.css         # Tema oscuro profesional
│       ├── css/login.css        # Estilos de login
│       ├── js/main.js           # Modal, toast, sidebar
│       └── js/kanban.js         # Drag & drop, CRUD tareas
├── seed.py                      # Datos iniciales + usuario admin
└── requirements.txt
```

---

## Instalación y ejecución

### 1. Clonar / descomprimir el proyecto

```bash
cd devtrack
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Cargar datos iniciales

```bash
python seed.py
```

### 5. Iniciar servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Acceder

```
http://localhost:8000/login
```

---

## Credenciales de acceso

```
Email    : admin@devtrack.io
Password : Admin2024!
```

---

## Endpoints

### Páginas (HTML)

| Método | Ruta              | Descripción              |
|--------|-------------------|--------------------------|
| GET    | `/login`          | Pantalla de login        |
| POST   | `/login`          | Submit de credenciales   |
| GET    | `/logout`         | Cerrar sesión            |
| GET    | `/`               | Dashboard con estadísticas |
| GET    | `/projects`       | Listado de proyectos     |
| POST   | `/projects/create`| Crear proyecto           |
| POST   | `/projects/{id}/edit`    | Editar proyecto   |
| POST   | `/projects/{id}/archive` | Archivar/restaurar|
| POST   | `/projects/{id}/delete`  | Eliminar proyecto |
| GET    | `/kanban`         | Tablero Kanban           |
| GET    | `/kanban?project_id=N`   | Kanban filtrado   |
| GET    | `/labels`         | Gestión de labels        |

### API REST (JSON)

| Método | Ruta                    | Descripción              |
|--------|-------------------------|--------------------------|
| GET    | `/api/projects`         | Lista proyectos activos  |
| GET    | `/api/labels`           | Lista labels             |
| POST   | `/api/labels`           | Crear label              |
| DELETE | `/api/labels/{id}`      | Eliminar label           |
| GET    | `/api/tasks/{id}`       | Obtener tarea            |
| POST   | `/api/tasks`            | Crear tarea              |
| PUT    | `/api/tasks/{id}`       | Actualizar tarea/estado  |
| DELETE | `/api/tasks/{id}`       | Eliminar tarea           |
| POST   | `/api/subtasks`         | Crear subtarea           |
| PUT    | `/api/subtasks/{id}`    | Actualizar subtarea      |
| DELETE | `/api/subtasks/{id}`    | Eliminar subtarea        |
| GET    | `/api/docs`             | Swagger UI               |

---

## Modelos de base de datos

```
User ──────────────────────────┐
  id, email, hashed_password   │
  full_name, is_admin           │
                                │
Project ───────────────────────┤ owner_id → User
  id, name, description        │
  color, is_archived            │
                                │
Task ──────────────────────────┤ project_id → Project
  id, title, description       │
  status (backlog/todo/         │
    in_progress/paused/done)   │
  priority (low/medium/         │
    high/critical)             │
  position, due_date           │
                                │
SubTask ────────────────────── │ task_id → Task
  id, title, is_done           │
                                │
Label ─────────────────────────┤
  id, name, color              │
                                │
TaskLabel ──────────────────── │ task_id + label_id (M2M)
                                │
ActivityLog ─────────────────── user_id → User, task_id → Task
  action, detail, created_at
```

---

## Funcionalidades

- **Autenticación**: Login con JWT en cookie httponly, rutas protegidas
- **Proyectos**: CRUD completo, color personalizable, archivar/restaurar
- **Kanban**: 5 columnas (Backlog → Done), drag & drop nativo HTML5
- **Tareas**: Crear, editar, eliminar, prioridad, fecha límite, labels
- **Subtareas**: Checklist con progreso visual por tarea
- **Labels**: Colores personalizables, asignación múltiple por tarea
- **Dashboard**: Estadísticas globales, progreso por proyecto, actividad reciente
- **Activity Log**: Registro automático de cambios de estado y creaciones
- **Responsive**: Sidebar colapsable en mobile

---

## Escalar a SaaS — Hoja de ruta

### Fase 1 — Multiusuario
- Agregar modelo `Workspace` / `Organization`
- Row-level security: filtrar queries por `workspace_id`
- Registro público + email de verificación
- Invitaciones por email con tokens firmados

### Fase 2 — Billing
- Integrar **Stripe** con planes (Free/Pro/Team)
- Tabla `Subscription` con estado y período
- Webhooks para sincronizar eventos de pago
- Feature flags por plan

### Fase 3 — Infraestructura
- Migrar SQLite → **PostgreSQL** (cambiar `DATABASE_URL`)
- Deploy en Railway / Render / Fly.io
- Variables de entorno con `.env` + `pydantic-settings`
- HTTPS con certificado SSL
- Backups automáticos de DB

### Fase 4 — IA (ideas)
- **Auto-priorización**: clasificar tareas por urgencia con LLM
- **Estimación de esfuerzo**: predecir duración basado en historial
- **Sugerencias de subtareas**: generar checklist automático
- **Resumen de progreso**: reporte semanal generado con IA
- **Búsqueda semántica**: encontrar tareas por significado, no solo texto

---

## Atajos de teclado

| Tecla | Acción                          |
|-------|---------------------------------|
| `N`   | Nueva tarea (en kanban)         |
| `Esc` | Cerrar modal activo             |

---

## Licencia

Uso personal y de portafolio.
#
