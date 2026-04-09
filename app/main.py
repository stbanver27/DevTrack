from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.db.database import init_db
from app.routes import auth, dashboard, projects, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    lifespan=lifespan,
)

# ── Static files & templates ──────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, tags=["Auth"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(projects.router, tags=["Projects"])
app.include_router(tasks.router, tags=["Tasks"])


# ── 404 handler ───────────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found(request: Request, exc):
    return templates.TemplateResponse("partials/404.html", {"request": request}, status_code=404)
