from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db


router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")

    # Обычный пользователь: главная = профиль
    if user and user.get("role") == "user":
        return RedirectResponse(url="/профиль", status_code=303)  # [web:305][web:119]

    stats = None
    if user:
        orders_count = db.execute(text("SELECT COUNT(*) FROM orders")).scalar_one()
        total_revenue = db.execute(text("SELECT COALESCE(SUM(total_amount), 0) FROM orders")).scalar_one()
        stats = {"orders_count": orders_count, "total_revenue": total_revenue}

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "user": user, "title": "Главная", "stats": stats},
    )
