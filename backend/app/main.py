from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from .config import settings
from .routers import auth, pages, admin, orders, reports, views_input, search, dictionaries, profile, user_orders

BASE_DIR = Path(__file__).resolve().parent  # .../backend/app
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))  # [web:34][web:35]

app = FastAPI(title="БД ресторана", docs_url="/docs", redoc_url=None)

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

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code in (401, 403):
        return templates.TemplateResponse(
            "errors/auth_required.html",
            {"request": request, "status_code": exc.status_code},
            status_code=exc.status_code,
        )
    return templates.TemplateResponse(
        "errors/http_error.html",
        {"request": request, "status_code": exc.status_code},
        status_code=exc.status_code,
    )

# Маршруты страниц
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(admin.router)
app.include_router(orders.router)
app.include_router(reports.router)
app.include_router(views_input.router)
app.include_router(search.router)
app.include_router(dictionaries.router)
app.include_router(profile.router)
app.include_router(user_orders.router)