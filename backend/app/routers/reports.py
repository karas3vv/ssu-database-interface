from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_login

router = APIRouter(prefix="/отчёты", tags=["Отчёты"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("", response_class=HTMLResponse)
def reports_index(request: Request):
    user = require_login(request)
    return templates.TemplateResponse("reports/index.html", {"request": request, "user": user, "title": "Отчёты"})


@router.post("/выручка", response_class=HTMLResponse)
def report_revenue(
    request: Request,
    db: Session = Depends(get_db),
    date_from: str = Form(...),
    date_to: str = Form(...),
):
    user = require_login(request)
    value = db.execute(
        text("SELECT get_revenue(CAST(:d1 AS date), CAST(:d2 AS date)) AS revenue"),
        {"d1": date_from, "d2": date_to},
    ).mappings().first()


    return templates.TemplateResponse(
        "reports/result_table.html",
        {
            "request": request,
            "user": user,
            "title": "Выручка за период",
            "columns": [("revenue", "Выручка")],
            "rows": [value] if value else [{"revenue": 0}],
            "back_url": "/отчёты",
        },
    )


@router.post("/продажи-блюд", response_class=HTMLResponse)
def report_dishes_sales(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    rows = db.execute(text("SELECT * FROM dishes_sales()")).mappings().all()

    return templates.TemplateResponse(
        "reports/result_table.html",
        {
            "request": request,
            "user": user,
            "title": "Продажи блюд",
            "columns": [
                ("dish_name", "Блюдо"),
                ("total_sold", "Продано (шт.)"),
                ("total_revenue", "Выручка"),
                ("avg_price", "Средняя сумма позиции"),
            ],
            "rows": rows,
            "back_url": "/отчёты",
        },
    )

@router.post("/заказы-гостя", response_class=HTMLResponse)
def report_guest_orders(
    request: Request,
    db: Session = Depends(get_db),
    guest_id: int = Form(...),
):
    user = require_login(request)

    rows = db.execute(
        text("SELECT * FROM guest_orders(:guest_id)"),
        {"guest_id": guest_id},
    ).mappings().all()

    columns = [
        ("id", "Номер заказа"),
        ("guest_id", "Гость"),
        ("table_id", "Стол"),
        ("waiter_id", "Официант"),
        ("order_time", "Время"),
        ("total_amount", "Сумма"),
        ("status", "Статус"),
        ("booking_id", "Бронирование"),
    ]

    return templates.TemplateResponse(
        "reports/result_table.html",
        {"request": request, "user": user, "title": "Заказы гостя", "columns": columns, "rows": rows, "back_url": "/отчёты"},
    )


@router.post("/свободные-столы", response_class=HTMLResponse)
def report_free_tables(
    request: Request,
    db: Session = Depends(get_db),
    date: str = Form(...),
    start: str = Form(...),
    end: str = Form(...),
    guests: int = Form(...),
):
    user = require_login(request)

    rows = db.execute(
        text("""
            SELECT * 
            FROM free_tables(
                CAST(:d AS date),
                CAST(:s AS time),
                CAST(:e AS time),
                CAST(:g AS int)
            )
        """),
        {"d": date, "s": start, "e": end, "g": guests},
    ).mappings().all()


    columns = [
        ("id", "Идентификатор"),
        ("table_number", "Номер стола"),
        ("seats", "Мест"),
        ("status", "Статус"),
    ]

    return templates.TemplateResponse(
        "reports/result_table.html",
        {"request": request, "user": user, "title": "Свободные столы", "columns": columns, "rows": rows, "back_url": "/отчёты"},
    )


@router.post("/статистика-гостей", response_class=HTMLResponse)
def report_guest_statistics(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = Form(10),
):
    user = require_login(request)

    rows = db.execute(
        text("SELECT * FROM guest_statistics(:limit)"),
        {"limit": limit},
    ).mappings().all()

    columns = [
        ("guest_id", "Гость (идентификатор)"),
        ("full_name", "Гость"),
        ("total_orders", "Заказов"),
        ("total_revenue", "Выручка"),
        ("avg_check", "Средний чек"),
    ]

    return templates.TemplateResponse(
        "reports/result_table.html",
        {"request": request, "user": user, "title": "Статистика гостей", "columns": columns, "rows": rows, "back_url": "/отчёты"},
    )


@router.post("/списать-продукты", response_class=HTMLResponse)
def action_consume_products(
    request: Request,
    db: Session = Depends(get_db),
    order_id: int = Form(...),
):
    user = require_login(request)

    # Важно: функция меняет данные, поэтому коммитим.
    row = db.execute(text("SELECT consume_products(:order_id) AS result"), {"order_id": order_id}).mappings().first()
    db.commit()

    columns = [("result", "Результат")]
    rows = [row] if row else [{"result": "Операция выполнена."}]

    return templates.TemplateResponse(
        "reports/result_table.html",
        {"request": request, "user": user, "title": "Списание продуктов по заказу", "columns": columns, "rows": rows, "back_url": "/отчёты"},
    )
