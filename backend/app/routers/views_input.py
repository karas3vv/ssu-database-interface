from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_admin

router = APIRouter(prefix="/ввод-через-представление", tags=["Ввод через представление"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("", response_class=HTMLResponse)
def order_entry_form(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    guests = db.execute(text("SELECT id, last_name, first_name FROM guests ORDER BY last_name, first_name")).mappings().all()
    tables_ = db.execute(text("SELECT id, table_number FROM tables ORDER BY table_number")).mappings().all()
    waiters = db.execute(text("SELECT id, last_name, first_name FROM waiters ORDER BY last_name, first_name")).mappings().all()
    return templates.TemplateResponse(
        "views/order_entry.html",
        {"request": request, "user": user, "guests": guests, "tables": tables_, "waiters": waiters, "title": "Ввод заказа через представление"},
    )


@router.post("")
def order_entry_submit(
    request: Request,
    db: Session = Depends(get_db),
    guest_id: int = Form(...),
    table_id: str = Form(""),
    waiter_id: str = Form(""),
    total_amount: str = Form("0"),
    status: str = Form("new"),
    booking_id: str = Form(""),
):
    require_admin(request)

    db.execute(
        text(
            """
            INSERT INTO v_order_entry (guest_id, table_id, waiter_id, order_time, total_amount, status, booking_id)
            VALUES (:guest_id,
                    NULLIF(:table_id,'')::int,
                    NULLIF(:waiter_id,'')::int,
                    :order_time,
                    :total_amount::numeric,
                    :status,
                    NULLIF(:booking_id,'')::int)
            """
        ),
        {
            "guest_id": guest_id,
            "table_id": table_id,
            "waiter_id": waiter_id,
            "order_time": datetime.now(),
            "total_amount": total_amount,
            "status": status.strip(),
            "booking_id": booking_id,
        },
    )
    db.commit()
    return RedirectResponse(url="/заказы", status_code=303)
