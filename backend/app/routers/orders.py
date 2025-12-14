from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from ..db import get_db
from ..deps import require_login, require_admin


router = APIRouter(prefix="/заказы", tags=["Заказы"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("", response_class=HTMLResponse)
def orders_list(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Query(50),
):
    user = require_login(request)
    limit = max(10, min(limit, 200))

    rows = db.execute(
        text(
            """
            SELECT
              o.id,
              o.order_time,
              o.status,
              o.total_amount,
              g.last_name || ' ' || g.first_name AS guest_name,
              t.table_number AS table_number,
              w.last_name || ' ' || w.first_name AS waiter_name
            FROM orders o
            LEFT JOIN guests g ON g.id = o.guest_id
            LEFT JOIN tables t ON t.id = o.table_id
            LEFT JOIN waiters w ON w.id = o.waiter_id
            ORDER BY o.id DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()

    next_cursor = rows[-1]["id"] if rows else None
    has_more = len(rows) == limit

    return templates.TemplateResponse(
        "orders/list.html",
        {
            "request": request,
            "user": user,
            "title": "Заказы",
            "rows": rows,
            "allow_edit": user.get("role") == "admin",
            "limit": limit,
            "next_cursor": next_cursor,
            "has_more": has_more,
        },
    )


@router.get("/кусок", response_class=HTMLResponse)
def orders_chunk(
    request: Request,
    db: Session = Depends(get_db),
    cursor: int = Query(...),
    limit: int = Query(50),
):
    user = require_login(request)
    limit = max(10, min(limit, 200))

    rows = db.execute(
        text(
            """
            SELECT
              o.id,
              o.order_time,
              o.status,
              o.total_amount,
              g.last_name || ' ' || g.first_name AS guest_name,
              t.table_number AS table_number,
              w.last_name || ' ' || w.first_name AS waiter_name
            FROM orders o
            LEFT JOIN guests g ON g.id = o.guest_id
            LEFT JOIN tables t ON t.id = o.table_id
            LEFT JOIN waiters w ON w.id = o.waiter_id
            WHERE o.id < :cursor
            ORDER BY o.id DESC
            LIMIT :limit
            """
        ),
        {"cursor": cursor, "limit": limit},
    ).mappings().all()

    next_cursor = rows[-1]["id"] if rows else None
    has_more = len(rows) == limit

    return templates.TemplateResponse(
        "orders/_rows.html",
        {
            "request": request,
            "user": user,
            "rows": rows,
            "allow_edit": user.get("role") == "admin",
            "limit": limit,
            "next_cursor": next_cursor,
            "has_more": has_more,
        },
    )


@router.get("/создать", response_class=HTMLResponse)
def order_create_form(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)

    tables_ = db.execute(text("SELECT id, table_number FROM tables ORDER BY table_number")).mappings().all()
    waiters = db.execute(text("SELECT id, last_name, first_name FROM waiters ORDER BY last_name, first_name")).mappings().all()

    return templates.TemplateResponse(
        "orders/create_with_guest.html",
        {
            "request": request,
            "user": user,
            "title": "Создать заказ",
            "tables": tables_,
            "waiters": waiters,
        },
    )


@router.post("/создать")
def order_create(
    request: Request,
    db: Session = Depends(get_db),

    # гость руками
    guest_last_name: str = Form(...),
    guest_first_name: str = Form(...),
    guest_middle_name: str = Form(""),

    # опционально аккаунт
    create_user: str = Form("0"),
    login: str = Form(""),
    password: str = Form(""),
    role: str = Form("user"),

    # заказ
    table_id: str = Form(""),
    waiter_id: str = Form(""),
    total_amount: str = Form("0"),
    status: str = Form("создан"),
    booking_id: str = Form(""),
):
    require_admin(request)

    # сумма
    try:
        total_amount_num = float((total_amount or "0").replace(",", "."))
    except ValueError:
        total_amount_num = 0.0

    # статус
    STATUS_MAP = {
        "new": "создан",
        "created": "создан",
        "paid": "оплачен",
        "cancelled": "отменён",
        "создан": "создан",
        "оплачен": "оплачен",
        "отменён": "отменён",
    }
    status_ru = STATUS_MAP.get((status or "").strip().lower(), "создан")

    # 1) создаём гостя
    guest_id = db.execute(
        text("""
            INSERT INTO guests (last_name, first_name, middle_name, birth_date, total_orders, total_discount)
            VALUES (:ln, :fn, NULLIF(:mn, ''), NULL, 0, 0)
            RETURNING id
        """),
        {
            "ln": guest_last_name.strip(),
            "fn": guest_first_name.strip(),
            "mn": guest_middle_name.strip(),
        },
    ).scalar_one()

    # 2) опционально создаём аккаунт (пароль -> bcrypt hash)
    if (create_user or "").strip() == "1":
        role_norm = (role or "user").strip().lower()
        if role_norm not in ("admin", "user"):
            role_norm = "user"

        if not login.strip():
            raise ValueError("login is required")
        if not password:
            raise ValueError("password is required")

        password_hash = bcrypt.hash(password)

        db.execute(
            text("""
                INSERT INTO users (login, password_hash, role)
                VALUES (:login, :ph, :role)
            """),
            {"login": login.strip(), "ph": password_hash, "role": role_norm},
        )

    # 3) создаём заказ
    order_id = db.execute(
        text("""
            INSERT INTO orders(guest_id, table_id, waiter_id, order_time, total_amount, status, booking_id)
            VALUES (:guest_id,
                    NULLIF(:table_id,'')::int,
                    NULLIF(:waiter_id,'')::int,
                    :order_time,
                    :total_amount,
                    :status,
                    NULLIF(:booking_id,'')::int)
            RETURNING id
        """),
        {
            "guest_id": guest_id,
            "table_id": table_id,
            "waiter_id": waiter_id,
            "order_time": datetime.now(),
            "total_amount": total_amount_num,
            "status": status_ru,
            "booking_id": booking_id,
        },
    ).scalar_one()

    db.commit()
    return RedirectResponse(url=f"/заказы/{order_id}", status_code=303)


@router.get("/{order_id}", response_class=HTMLResponse)
def order_edit(order_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_login(request)

    order = db.execute(
        text("SELECT id, guest_id, table_id, waiter_id, status, total_amount, order_time FROM orders WHERE id=:id"),
        {"id": order_id},
    ).mappings().first()

    if not order:
        return templates.TemplateResponse(
            "message.html",
            {"request": request, "user": user, "title": "Ошибка", "message": "Заказ не найден."},
            status_code=404,
        )

    items = db.execute(
        text(
            """
            SELECT
              oi.dish_id,
              d.name AS dish_name,
              d.price,
              oi.quantity,
              (oi.quantity * d.price) AS amount
            FROM order_items oi
            JOIN dishes d ON d.id = oi.dish_id
            WHERE oi.order_id = :order_id
            ORDER BY d.name
            """
        ),
        {"order_id": order_id},
    ).mappings().all()

    guests = db.execute(text("SELECT id, last_name, first_name FROM guests ORDER BY last_name, first_name")).mappings().all()
    tables_ = db.execute(text("SELECT id, table_number FROM tables ORDER BY table_number")).mappings().all()
    waiters = db.execute(text("SELECT id, last_name, first_name FROM waiters ORDER BY last_name, first_name")).mappings().all()
    dishes_ = db.execute(text("SELECT id, name, price FROM dishes ORDER BY name")).mappings().all()

    return templates.TemplateResponse(
        "orders/edit.html",
        {
            "request": request,
            "user": user,
            "title": f"Заказ №{order_id}",
            "action": f"/заказы/{order_id}/сохранить",
            "order": order,
            "guests": guests,
            "tables": tables_,
            "waiters": waiters,
            "items": items,
            "dishes": dishes_,
            "allow_edit": user.get("role") == "admin",
        },
    )


@router.post("/{order_id}/сохранить")
def order_save(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    guest_id: int = Form(...),
    table_id: str = Form(""),
    waiter_id: str = Form(""),
    status: str = Form(""),
):
    require_admin(request)

    db.execute(
        text(
            """
            UPDATE orders
            SET guest_id=:guest_id,
                table_id=NULLIF(:table_id,'')::int,
                waiter_id=NULLIF(:waiter_id,'')::int,
                status=:status
            WHERE id=:id
            """
        ),
        {"id": order_id, "guest_id": guest_id, "table_id": table_id, "waiter_id": waiter_id, "status": status.strip()},
    )
    db.commit()
    return RedirectResponse(url=f"/заказы/{order_id}", status_code=303)


@router.post("/{order_id}/позиция/добавить")
def order_item_add(
    order_id: int,
    request: Request,
    db: Session = Depends(get_db),
    dish_id: int = Form(...),
    quantity: int = Form(...),
):
    require_admin(request)

    db.execute(
        text(
            """
            INSERT INTO order_items(order_id, dish_id, quantity)
            VALUES (:order_id, :dish_id, :quantity)
            ON CONFLICT (order_id, dish_id)
            DO UPDATE SET quantity = order_items.quantity + EXCLUDED.quantity
            """
        ),
        {"order_id": order_id, "dish_id": dish_id, "quantity": quantity},
    )
    db.commit()
    return RedirectResponse(url=f"/заказы/{order_id}", status_code=303)


@router.post("/{order_id}/позиция/изменить/{dish_id}")
def order_item_update(
    order_id: int,
    dish_id: int,
    request: Request,
    db: Session = Depends(get_db),
    quantity: int = Form(...),
):
    require_admin(request)

    db.execute(
        text(
            """
            UPDATE order_items
            SET quantity=:quantity
            WHERE order_id=:order_id AND dish_id=:dish_id
            """
        ),
        {"order_id": order_id, "dish_id": dish_id, "quantity": quantity},
    )
    db.commit()
    return RedirectResponse(url=f"/заказы/{order_id}", status_code=303)


@router.post("/{order_id}/позиция/удалить/{dish_id}")
def order_item_delete(order_id: int, dish_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(
        text("DELETE FROM order_items WHERE order_id=:order_id AND dish_id=:dish_id"),
        {"order_id": order_id, "dish_id": dish_id},
    )
    db.commit()
    return RedirectResponse(url=f"/заказы/{order_id}", status_code=303)
