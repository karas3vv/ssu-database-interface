from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .routers import auth, pages, admin, orders, reports, views_input, search

BASE_DIR = Path(__file__).resolve().parent  # .../backend/app

app = FastAPI(title="Интерфейс базы данных ресторана", docs_url="/docs", redoc_url=None)

# Сессии (для входа и роли)
app.add_middleware(
    SessionMiddleware,
    secret_key=str(settings.SECRET_KEY),
    session_cookie="s",
    same_site="lax",
    https_only=False,
)

# Статика (CSS)
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

# Маршруты страниц
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(admin.router)
app.include_router(orders.router)
app.include_router(reports.router)
# app.include_router(views_input.router)
app.include_router(search.router)