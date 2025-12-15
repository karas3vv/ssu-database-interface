from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user

router = APIRouter(tags=["Профиль"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@router.get("/профиль", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)

    # Берём guest_id, чтобы понимать "чьи" заказы
    row = db.execute(
        text("SELECT guest_id FROM users WHERE id = :uid"),
        {"uid": user["id"]},
    ).mappings().first()

    guest_id = row["guest_id"] if row else None

    stats = {"orders_count": 0, "total_spent": 0}
    orders = []

    if guest_id is not None:
        stats = db.execute(
            text("""
                SELECT
                  COUNT(*) AS orders_count,
                  COALESCE(SUM(total_amount), 0) AS total_spent
                FROM orders
                WHERE guest_id = :guest_id
            """),
            {"guest_id": guest_id},
        ).mappings().first() or stats

        orders = db.execute(
            text("""
                SELECT id, order_time, total_amount, status
                FROM orders
                WHERE guest_id = :guest_id
                ORDER BY order_time DESC
                LIMIT 50
            """),
            {"guest_id": guest_id},
        ).mappings().all()

    return templates.TemplateResponse(
        "profile/profile.html",
        {
            "request": request,
            "title": "Профиль",
            "user": user,
            "stats": stats,
            "orders": orders,
        },
    )
