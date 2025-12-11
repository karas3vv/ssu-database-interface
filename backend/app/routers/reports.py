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
        text("SELECT get_revenue(:d1::date, :d2::date) AS revenue"),
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
