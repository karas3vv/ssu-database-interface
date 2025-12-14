from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from ..db import get_db
from ..deps import require_admin


router = APIRouter(prefix="/ввод-через-представление", tags=["Добавить гостя"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("", response_class=HTMLResponse)
def order_entry_form(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    tables_ = db.execute(text("SELECT id, table_number FROM tables ORDER BY table_number")).mappings().all()
    waiters = db.execute(text("SELECT id, last_name, first_name FROM waiters ORDER BY last_name, first_name")).mappings().all()

    return templates.TemplateResponse(
        "views/order_entry.html",
        {
            "request": request,
            "user": user,
            "tables": tables_,
            "waiters": waiters,
            "title": "Ввод заказа (создание гостя вручную)",
        },
    )


@router.post("")
def order_entry_submit(
    request: Request,
    db: Session = Depends(get_db),

    # гость руками
    guest_last_name: str = Form(...),
    guest_first_name: str = Form(...),
    guest_middle_name: str = Form(""),

    # опционально аккаунт
    create_user: str = Form("0"),      # hidden=0 + checkbox value=1
    login: str = Form(""),
    password: str = Form(""),          # <-- было password_hash
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

    # 2) опционально создаём аккаунт (логин + ПАРОЛЬ -> bcrypt hash)
    if (create_user or "").strip() == "1":
        role_norm = (role or "user").strip().lower()
        if role_norm not in ("admin", "user"):
            role_norm = "user"

        if not login.strip():
            raise HTTPException(status_code=400, detail="Логин обязателен, если создаёшь аккаунт")
        if not password:
            raise HTTPException(status_code=400, detail="Пароль обязателен, если создаёшь аккаунт")

        password_hash = bcrypt.hash(password)  # <-- создаём хэш [web:992]

        db.execute(
            text("""
                INSERT INTO users (login, password_hash, role)
                VALUES (:login, :ph, :role)
            """),
            {
                "login": login.strip(),
                "ph": password_hash,
                "role": role_norm,
            },
        )

    # 3) создаём заказ напрямую в orders (без view)
    db.execute(
        text("""
            INSERT INTO orders
              (guest_id, table_id, waiter_id, order_time, total_amount, status, booking_id)
            VALUES
              (:guest_id,
               NULLIF(:table_id, '')::int,
               NULLIF(:waiter_id, '')::int,
               :order_time,
               :total_amount,
               :status,
               NULLIF(:booking_id, '')::int)
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
    )

    db.commit()
    return RedirectResponse(url="/заказы", status_code=303)
