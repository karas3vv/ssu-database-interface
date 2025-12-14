from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..errors import safe_commit
from ..deps import require_login, require_admin


router = APIRouter(prefix="/справочники", tags=["Справочники"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def render_db_error(request: Request, back_url: str, message: str, status_code: int = 400):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "user": request.session.get("user"),
            "message": message,
            "back_url": back_url,
        },
        status_code=status_code,
    )


@router.get("", response_class=HTMLResponse)
def dictionaries_index(request: Request):
    user = require_login(request)
    return templates.TemplateResponse(
        "admin/index.html",
        {"request": request, "user": user, "title": "Справочники"},
    )


@router.get("/блюда", response_class=HTMLResponse)
def dishes_list(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    rows = db.execute(
        text("SELECT id, name, category, price, country_of_origin FROM dishes ORDER BY id")
    ).mappings().all()

    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "user": user,
            "title": "Справочник: блюда",
            "entity_title": "Блюда",
            "columns": [
                ("id", "Идентификатор"),
                ("name", "Наименование"),
                ("category", "Категория"),
                ("price", "Цена"),
                ("country_of_origin", "Страна происхождения"),
            ],
            "rows": rows,
            "create_url": "/справочники/блюда/добавить",
            "edit_url_prefix": "/справочники/блюда/изменить/",
            "delete_url_prefix": "/справочники/блюда/удалить/",
            "allow_edit": user.get("role") == "admin",
        },
    )


@router.get("/блюда/добавить", response_class=HTMLResponse)
def dishes_create_form(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse(
        "admin/edit.html",
        {
            "request": request,
            "user": user,
            "title": "Добавить блюдо",
            "action": "/справочники/блюда/добавить",
            "values": {"name": "", "category": "", "price": "", "country_of_origin": ""},
        },
    )


@router.post("/блюда/добавить", response_class=HTMLResponse)
def dishes_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    category: str = Form(""),
    price: str = Form(...),
    country_of_origin: str = Form(""),
):
    require_admin(request)

    db.execute(
        text(
            """
            INSERT INTO dishes(name, category, price, country_of_origin)
            VALUES (:name, NULLIF(:category,''), :price::numeric, NULLIF(:country_of_origin,''))
            """
        ),
        {
            "name": name.strip(),
            "category": category.strip(),
            "price": price,
            "country_of_origin": country_of_origin.strip(),
        },
    )

    err = safe_commit(db)
    if err:
        return render_db_error(request, "/справочники/блюда", err)

    return RedirectResponse(url="/справочники/блюда", status_code=303)


@router.get("/блюда/изменить/{dish_id}", response_class=HTMLResponse)
def dishes_edit_form(dish_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)

    row = db.execute(
        text("SELECT id, name, category, price, country_of_origin FROM dishes WHERE id=:id"),
        {"id": dish_id},
    ).mappings().first()

    if not row:
        return render_db_error(request, "/справочники/блюда", "Запись не найдена.", status_code=404)

    return templates.TemplateResponse(
        "admin/edit.html",
        {
            "request": request,
            "user": user,
            "title": "Изменить блюдо",
            "action": f"/справочники/блюда/изменить/{dish_id}",
            "values": row,
        },
    )


@router.post("/блюда/изменить/{dish_id}", response_class=HTMLResponse)
def dishes_edit(
    dish_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    category: str = Form(""),
    price: str = Form(...),
    country_of_origin: str = Form(""),
):
    require_admin(request)

    db.execute(
        text(
            """
            UPDATE dishes
            SET name=:name,
                category=NULLIF(:category,''),
                price=:price::numeric,
                country_of_origin=NULLIF(:country_of_origin,'')
            WHERE id=:id
            """
        ),
        {
            "id": dish_id,
            "name": name.strip(),
            "category": category.strip(),
            "price": price,
            "country_of_origin": country_of_origin.strip(),
        },
    )

    err = safe_commit(db)
    if err:
        return render_db_error(request, f"/справочники/блюда/изменить/{dish_id}", err)

    return RedirectResponse(url="/справочники/блюда", status_code=303)


@router.post("/блюда/удалить/{dish_id}", response_class=HTMLResponse)
def dishes_delete(dish_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)

    db.execute(text("DELETE FROM dishes WHERE id=:id"), {"id": dish_id})

    err = safe_commit(db)
    if err:
        return render_db_error(request, "/справочники/блюда", err)

    return RedirectResponse(url="/справочники/блюда", status_code=303)
