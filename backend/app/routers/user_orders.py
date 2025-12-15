from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user  # должен возвращать dict из session

router = APIRouter(tags=["Заказы пользователя"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _get_guest_id(db: Session, user_id: int) -> int:
    row = db.execute(
        text("SELECT guest_id FROM users WHERE id = :uid"),
        {"uid": user_id},
    ).mappings().first()
    return row["guest_id"] if row and row["guest_id"] is not None else None


@router.get("/заказ/создать", response_class=HTMLResponse)
def create_order_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)

    if user.get("role") != "user":
        return RedirectResponse(url="/", status_code=303)

    guest_id = _get_guest_id(db, user["id"])
    if guest_id is None:
        # нет привязки к гостю -> некуда записывать заказ
        return templates.TemplateResponse(
            "profile/profile.html",
            {"request": request, "user": user, "title": "Профиль", "error": "Для пользователя не задан guest_id."},
            status_code=400,
        )

    tables_ = db.execute(text("SELECT id, table_number FROM tables ORDER BY table_number")).mappings().all()
    return templates.TemplateResponse(
        "orders/create_order.html",
        {"request": request, "user": user, "title": "Создать заказ", "tables": tables_},
    )


@router.post("/заказ/создать")
def create_order_submit(
    request: Request,
    db: Session = Depends(get_db),
    table_id: str = Form(""),
):
    user = get_current_user(request)

    if user.get("role") != "user":
        return RedirectResponse(url="/", status_code=303)

    guest_id = _get_guest_id(db, user["id"])
    if guest_id is None:
        return RedirectResponse(url="/профиль", status_code=303)

    # Для демо: создаём заказ со статусом "new", сумма 0, waiter/booking пустые
    db.execute(
        text("""
            INSERT INTO orders (guest_id, table_id, waiter_id, order_time, total_amount, status, booking_id)
            VALUES (:guest_id,
                    NULLIF(:table_id,'')::int,
                    NULL,
                    :order_time,
                    0,
                    :status,
                    NULL)
        """),
        {
            "guest_id": guest_id,
            "table_id": table_id,
            "order_time": datetime.now(),
            "status": "new",
        },
    )
    db.commit()

    return RedirectResponse(url="/профиль", status_code=303)
