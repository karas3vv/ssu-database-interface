from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user

router = APIRouter(tags=["Позиции заказа"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def _ensure_user_order(db: Session, user: dict, order_id: int) -> bool:
    # доступ: только admin или владелец заказа (по guest_id)
    if user.get("role") == "admin":
        return True

    row = db.execute(
        text("""
            SELECT 1
            FROM orders o
            JOIN users u ON u.guest_id = o.guest_id
            WHERE o.id = :oid AND u.id = :uid
        """),
        {"oid": order_id, "uid": user["id"]},
    ).first()
    return row is not None


@router.get("/заказ/{order_id}", response_class=HTMLResponse)
def order_page(order_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request)

    if not _ensure_user_order(db, user, order_id):
        return RedirectResponse(url="/профиль", status_code=303)

    order = db.execute(
        text("SELECT id, order_time, total_amount, status FROM orders WHERE id = :oid"),
        {"oid": order_id},
    ).mappings().first()

    items = db.execute(
        text("""
            SELECT oi.id, d.name, oi.qty, oi.price, (oi.qty * oi.price) AS line_total
            FROM order_items oi
            JOIN dishes d ON d.id = oi.dish_id
            WHERE oi.order_id = :oid
            ORDER BY oi.id
        """),
        {"oid": order_id},
    ).mappings().all()

    dishes = db.execute(
        text("SELECT id, name, price FROM dishes ORDER BY name"),
    ).mappings().all()

    return templates.TemplateResponse(
        "orders/order_edit.html",
        {"request": request, "user": user, "title": f"Заказ #{order_id}", "order": order, "items": items, "dishes": dishes},
    )


@router.post("/заказ/{order_id}/добавить")
def add_item(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    dish_id: int = Form(...),
    qty: int = Form(...),
):
    user = get_current_user(request)

    if not _ensure_user_order(db, user, order_id):
        return RedirectResponse(url="/профиль", status_code=303)

    dish = db.execute(
        text("SELECT id, price FROM dishes WHERE id = :did"),
        {"did": dish_id},
    ).mappings().first()

    if not dish:
        return RedirectResponse(url=f"/заказ/{order_id}", status_code=303)

    # upsert: если блюдо уже есть в заказе — увеличиваем qty
    db.execute(
        text("""
            INSERT INTO order_items (order_id, dish_id, qty, price)
            VALUES (:oid, :did, :qty, :price)
            ON CONFLICT (order_id, dish_id)
            DO UPDATE SET qty = order_items.qty + EXCLUDED.qty
        """),
        {"oid": order_id, "did": dish_id, "qty": qty, "price": dish["price"]},
    )

    # пересчёт суммы
    db.execute(text("SELECT recalc_order_total(:oid)"), {"oid": order_id})
    db.commit()

    return RedirectResponse(url=f"/заказ/{order_id}", status_code=303)
