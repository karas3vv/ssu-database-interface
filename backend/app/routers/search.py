from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_login

router = APIRouter(prefix="/поиск", tags=["Поиск"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("", response_class=HTMLResponse)
def search_form(request: Request):
    user = require_login(request)
    return templates.TemplateResponse("search/index.html", {"request": request, "user": user, "title": "Поиск"})


@router.post("", response_class=HTMLResponse)
def search_results(
    request: Request,
    db: Session = Depends(get_db),
    guest_last_name: str = Form(""),
    status: str = Form(""),
    date_from: str = Form(""),
    date_to: str = Form(""),
):
    user = require_login(request)

    rows = db.execute(
        text(
            """
            SELECT
              o.id AS order_id,
              o.order_time,
              o.status,
              o.total_amount,
              g.last_name || ' ' || g.first_name AS guest_name,
              t.table_number,
              w.last_name || ' ' || w.first_name AS waiter_name,
              COALESCE(SUM(p.amount), 0) AS paid_amount
            FROM orders o
            LEFT JOIN guests g ON g.id = o.guest_id
            LEFT JOIN tables t ON t.id = o.table_id
            LEFT JOIN waiters w ON w.id = o.waiter_id
            LEFT JOIN payments p ON p.order_id = o.id
            WHERE (:ln = '' OR g.last_name ILIKE :ln_like)
              AND (:st = '' OR o.status = :st)
              AND (:d1 = '' OR o.order_time::date >= :d1::date)
              AND (:d2 = '' OR o.order_time::date <= :d2::date)
            GROUP BY o.id, o.order_time, o.status, o.total_amount, g.last_name, g.first_name, t.table_number, w.last_name, w.first_name
            ORDER BY o.order_time DESC
            LIMIT 200
            """
        ),
        {
            "ln": guest_last_name.strip(),
            "ln_like": f"%{guest_last_name.strip()}%",
            "st": status.strip(),
            "d1": date_from,
            "d2": date_to,
        },
    ).mappings().all()

    return templates.TemplateResponse(
        "search/result.html",
        {
            "request": request,
            "user": user,
            "title": "Результаты поиска",
            "rows": rows,
        },
    )
