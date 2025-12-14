from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import require_login, require_admin
from ..errors import safe_commit

router = APIRouter(prefix="/справочники", tags=["Справочники"])

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def render_error(request: Request, message: str, back_url: str, status_code: int = 400):
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "user": request.session.get("user"), "message": message, "back_url": back_url},
        status_code=status_code,
    )


@router.get("", response_class=HTMLResponse)
def dictionaries_index(request: Request):
    user = require_login(request)
    return templates.TemplateResponse(
        "admin/index.html",
        {"request": request, "user": user, "title": "Справочники"},
    )


# Гости 

@router.get("/гости", response_class=HTMLResponse)
def guests_list(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    rows = db.execute(
        text("SELECT id, last_name, first_name, middle_name, birth_date FROM guests ORDER BY id")
    ).mappings().all()

    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "user": user,
            "title": "Справочник: гости",
            "entity_title": "Гости",
            "columns": [
                ("id", "Идентификатор"),
                ("last_name", "Фамилия"),
                ("first_name", "Имя"),
                ("middle_name", "Отчество"),
                ("birth_date", "Дата рождения"),
            ],
            "rows": rows,
            "create_url": "/справочники/гости/добавить",
            "edit_url_prefix": "/справочники/гости/изменить/",
            "delete_url_prefix": "/справочники/гости/удалить/",
            "allow_edit": user.get("role") == "admin",
        },
    )


@router.get("/гости/добавить", response_class=HTMLResponse)
def guests_create_form(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse(
        "admin/edit_guest.html",
        {"request": request, "user": user, "title": "Добавить гостя", "action": "/справочники/гости/добавить", "values": {}},
    )


@router.post("/гости/добавить", response_class=HTMLResponse)
def guests_create(
    request: Request,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(""),
    birth_date: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            INSERT INTO guests(last_name, first_name, middle_name, birth_date)
            VALUES (:ln, :fn, NULLIF(:mn,''), NULLIF(:bd,'')::date)
            """
        ),
        {"ln": last_name.strip(), "fn": first_name.strip(), "mn": middle_name.strip(), "bd": birth_date},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/гости")
    return RedirectResponse(url="/справочники/гости", status_code=303)


@router.get("/гости/изменить/{guest_id}", response_class=HTMLResponse)
def guests_edit_form(guest_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    row = db.execute(
        text("SELECT id, last_name, first_name, middle_name, birth_date FROM guests WHERE id=:id"),
        {"id": guest_id},
    ).mappings().first()

    if not row:
        return render_error(request, "Запись не найдена.", "/справочники/гости", status_code=404)

    return templates.TemplateResponse(
        "admin/edit_guest.html",
        {"request": request, "user": user, "title": "Изменить гостя", "action": f"/справочники/гости/изменить/{guest_id}", "values": row},
    )


@router.post("/гости/изменить/{guest_id}", response_class=HTMLResponse)
def guests_edit(
    guest_id: int,
    request: Request,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(""),
    birth_date: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            UPDATE guests
            SET last_name=:ln,
                first_name=:fn,
                middle_name=NULLIF(:mn,''),
                birth_date=NULLIF(:bd,'')::date
            WHERE id=:id
            """
        ),
        {"id": guest_id, "ln": last_name.strip(), "fn": first_name.strip(), "mn": middle_name.strip(), "bd": birth_date},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, f"/справочники/гости/изменить/{guest_id}")
    return RedirectResponse(url="/справочники/гости", status_code=303)


@router.post("/гости/удалить/{guest_id}", response_class=HTMLResponse)
def guests_delete(guest_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(text("DELETE FROM guests WHERE id=:id"), {"id": guest_id})
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/гости")
    return RedirectResponse(url="/справочники/гости", status_code=303)


# Столы 

@router.get("/столы", response_class=HTMLResponse)
def tables_list(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    rows = db.execute(
        text("SELECT id, table_number, seats, status FROM tables ORDER BY table_number")
    ).mappings().all()

    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "user": user,
            "title": "Справочник: столы",
            "entity_title": "Столы",
            "columns": [
                ("id", "Идентификатор"),
                ("table_number", "Номер стола"),
                ("seats", "Мест"),
                ("status", "Статус"),
            ],
            "rows": rows,
            "create_url": "/справочники/столы/добавить",
            "edit_url_prefix": "/справочники/столы/изменить/",
            "delete_url_prefix": "/справочники/столы/удалить/",
            "allow_edit": user.get("role") == "admin",
        },
    )


@router.get("/столы/добавить", response_class=HTMLResponse)
def tables_create_form(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse(
        "admin/edit_table.html",
        {"request": request, "user": user, "title": "Добавить стол", "action": "/справочники/столы/добавить", "values": {}},
    )


@router.post("/столы/добавить", response_class=HTMLResponse)
def tables_create(
    request: Request,
    db: Session = Depends(get_db),
    table_number: int = Form(...),
    seats: int = Form(...),
    status: str = Form("free"),
):
    require_admin(request)
    db.execute(
        text("INSERT INTO tables(table_number, seats, status) VALUES (:n, :s, :st)"),
        {"n": table_number, "s": seats, "st": status.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/столы")
    return RedirectResponse(url="/справочники/столы", status_code=303)


@router.get("/столы/изменить/{table_id}", response_class=HTMLResponse)
def tables_edit_form(table_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    row = db.execute(
        text("SELECT id, table_number, seats, status FROM tables WHERE id=:id"),
        {"id": table_id},
    ).mappings().first()

    if not row:
        return render_error(request, "Запись не найдена.", "/справочники/столы", status_code=404)

    return templates.TemplateResponse(
        "admin/edit_table.html",
        {"request": request, "user": user, "title": "Изменить стол", "action": f"/справочники/столы/изменить/{table_id}", "values": row},
    )


@router.post("/столы/изменить/{table_id}", response_class=HTMLResponse)
def tables_edit(
    table_id: int,
    request: Request,
    db: Session = Depends(get_db),
    table_number: int = Form(...),
    seats: int = Form(...),
    status: str = Form("free"),
):
    require_admin(request)
    db.execute(
        text("UPDATE tables SET table_number=:n, seats=:s, status=:st WHERE id=:id"),
        {"id": table_id, "n": table_number, "s": seats, "st": status.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, f"/справочники/столы/изменить/{table_id}")
    return RedirectResponse(url="/справочники/столы", status_code=303)


@router.post("/столы/удалить/{table_id}", response_class=HTMLResponse)
def tables_delete(table_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(text("DELETE FROM tables WHERE id=:id"), {"id": table_id})
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/столы")
    return RedirectResponse(url="/справочники/столы", status_code=303)


# Блюда

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
        {"name": name.strip(), "category": category.strip(), "price": price, "country_of_origin": country_of_origin.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/блюда")
    return RedirectResponse(url="/справочники/блюда", status_code=303)


@router.get("/блюда/изменить/{dish_id}", response_class=HTMLResponse)
def dishes_edit_form(dish_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    row = db.execute(
        text("SELECT id, name, category, price, country_of_origin FROM dishes WHERE id=:id"),
        {"id": dish_id},
    ).mappings().first()

    if not row:
        return render_error(request, "Запись не найдена.", "/справочники/блюда", status_code=404)

    return templates.TemplateResponse(
        "admin/edit.html",
        {"request": request, "user": user, "title": "Изменить блюдо", "action": f"/справочники/блюда/изменить/{dish_id}", "values": row},
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
        {"id": dish_id, "name": name.strip(), "category": category.strip(), "price": price, "country_of_origin": country_of_origin.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, f"/справочники/блюда/изменить/{dish_id}")
    return RedirectResponse(url="/справочники/блюда", status_code=303)


@router.post("/блюда/удалить/{dish_id}", response_class=HTMLResponse)
def dishes_delete(dish_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(text("DELETE FROM dishes WHERE id=:id"), {"id": dish_id})
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/блюда")
    return RedirectResponse(url="/справочники/блюда", status_code=303)


# Официанты 

@router.get("/официанты", response_class=HTMLResponse)
def waiters_list(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    rows = db.execute(
        text("SELECT id, last_name, first_name, middle_name, salary FROM waiters ORDER BY id")
    ).mappings().all()
    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "user": user,
            "title": "Справочник: официанты",
            "entity_title": "Официанты",
            "columns": [
                ("id", "Идентификатор"),
                ("last_name", "Фамилия"),
                ("first_name", "Имя"),
                ("middle_name", "Отчество"),
                ("salary", "Оклад"),
            ],
            "rows": rows,
            "create_url": "/справочники/официанты/добавить",
            "edit_url_prefix": "/справочники/официанты/изменить/",
            "delete_url_prefix": "/справочники/официанты/удалить/",
            "allow_edit": user.get("role") == "admin",
        },
    )


@router.get("/официанты/добавить", response_class=HTMLResponse)
def waiters_create_form(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse(
        "admin/edit_waiter.html",
        {"request": request, "user": user, "title": "Добавить официанта", "action": "/справочники/официанты/добавить", "values": {}},
    )


@router.post("/официанты/добавить", response_class=HTMLResponse)
def waiters_create(
    request: Request,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(""),
    salary: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            INSERT INTO waiters(last_name, first_name, middle_name, salary)
            VALUES (:ln, :fn, NULLIF(:mn,''), NULLIF(:sal,'')::numeric)
            """
        ),
        {"ln": last_name.strip(), "fn": first_name.strip(), "mn": middle_name.strip(), "sal": salary},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/официанты")
    return RedirectResponse(url="/справочники/официанты", status_code=303)


@router.get("/официанты/изменить/{waiter_id}", response_class=HTMLResponse)
def waiters_edit_form(waiter_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    row = db.execute(
        text("SELECT id, last_name, first_name, middle_name, salary FROM waiters WHERE id=:id"),
        {"id": waiter_id},
    ).mappings().first()

    if not row:
        return render_error(request, "Запись не найдена.", "/справочники/официанты", status_code=404)

    return templates.TemplateResponse(
        "admin/edit_waiter.html",
        {"request": request, "user": user, "title": "Изменить официанта", "action": f"/справочники/официанты/изменить/{waiter_id}", "values": row},
    )


@router.post("/официанты/изменить/{waiter_id}", response_class=HTMLResponse)
def waiters_edit(
    waiter_id: int,
    request: Request,
    db: Session = Depends(get_db),
    last_name: str = Form(...),
    first_name: str = Form(...),
    middle_name: str = Form(""),
    salary: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            UPDATE waiters
            SET last_name=:ln,
                first_name=:fn,
                middle_name=NULLIF(:mn,''),
                salary=NULLIF(:sal,'')::numeric
            WHERE id=:id
            """
        ),
        {"id": waiter_id, "ln": last_name.strip(), "fn": first_name.strip(), "mn": middle_name.strip(), "sal": salary},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, f"/справочники/официанты/изменить/{waiter_id}")
    return RedirectResponse(url="/справочники/официанты", status_code=303)


@router.post("/официанты/удалить/{waiter_id}", response_class=HTMLResponse)
def waiters_delete(waiter_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(text("DELETE FROM waiters WHERE id=:id"), {"id": waiter_id})
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/официанты")
    return RedirectResponse(url="/справочники/официанты", status_code=303)


# Поставщики

@router.get("/поставщики", response_class=HTMLResponse)
def suppliers_list(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    rows = db.execute(
        text("SELECT id, name, address, contact_person, phone, email FROM suppliers ORDER BY id")
    ).mappings().all()
    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "user": user,
            "title": "Справочник: поставщики",
            "entity_title": "Поставщики",
            "columns": [
                ("id", "Идентификатор"),
                ("name", "Название"),
                ("address", "Адрес"),
                ("contact_person", "Контактное лицо"),
                ("phone", "Телефон"),
                ("email", "Электронная почта"),
            ],
            "rows": rows,
            "create_url": "/справочники/поставщики/добавить",
            "edit_url_prefix": "/справочники/поставщики/изменить/",
            "delete_url_prefix": "/справочники/поставщики/удалить/",
            "allow_edit": user.get("role") == "admin",
        },
    )


@router.get("/поставщики/добавить", response_class=HTMLResponse)
def suppliers_create_form(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse(
        "admin/edit_supplier.html",
        {"request": request, "user": user, "title": "Добавить поставщика", "action": "/справочники/поставщики/добавить", "values": {}},
    )


@router.post("/поставщики/добавить", response_class=HTMLResponse)
def suppliers_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    address: str = Form(""),
    contact_person: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            INSERT INTO suppliers(name, address, contact_person, phone, email)
            VALUES (:name, NULLIF(:addr,''), NULLIF(:cp,''), NULLIF(:ph,''), NULLIF(:em,''))
            """
        ),
        {"name": name.strip(), "addr": address.strip(), "cp": contact_person.strip(), "ph": phone.strip(), "em": email.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/поставщики")
    return RedirectResponse(url="/справочники/поставщики", status_code=303)


@router.get("/поставщики/изменить/{supplier_id}", response_class=HTMLResponse)
def suppliers_edit_form(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    row = db.execute(
        text("SELECT id, name, address, contact_person, phone, email FROM suppliers WHERE id=:id"),
        {"id": supplier_id},
    ).mappings().first()

    if not row:
        return render_error(request, "Запись не найдена.", "/справочники/поставщики", status_code=404)

    return templates.TemplateResponse(
        "admin/edit_supplier.html",
        {"request": request, "user": user, "title": "Изменить поставщика", "action": f"/справочники/поставщики/изменить/{supplier_id}", "values": row},
    )


@router.post("/поставщики/изменить/{supplier_id}", response_class=HTMLResponse)
def suppliers_edit(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    address: str = Form(""),
    contact_person: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            UPDATE suppliers
            SET name=:name,
                address=NULLIF(:addr,''),
                contact_person=NULLIF(:cp,''),
                phone=NULLIF(:ph,''),
                email=NULLIF(:em,'')
            WHERE id=:id
            """
        ),
        {"id": supplier_id, "name": name.strip(), "addr": address.strip(), "cp": contact_person.strip(), "ph": phone.strip(), "em": email.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, f"/справочники/поставщики/изменить/{supplier_id}")
    return RedirectResponse(url="/справочники/поставщики", status_code=303)


@router.post("/поставщики/удалить/{supplier_id}", response_class=HTMLResponse)
def suppliers_delete(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(text("DELETE FROM suppliers WHERE id=:id"), {"id": supplier_id})
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/поставщики")
    return RedirectResponse(url="/справочники/поставщики", status_code=303)


# Продукты

@router.get("/продукты", response_class=HTMLResponse)
def products_list(request: Request, db: Session = Depends(get_db)):
    user = require_login(request)
    rows = db.execute(
        text("SELECT id, name, weight, expiry_date, quantity, category FROM products ORDER BY id")
    ).mappings().all()
    return templates.TemplateResponse(
        "admin/list.html",
        {
            "request": request,
            "user": user,
            "title": "Справочник: продукты",
            "entity_title": "Продукты",
            "columns": [
                ("id", "Идентификатор"),
                ("name", "Наименование"),
                ("weight", "Масса единицы"),
                ("expiry_date", "Срок годности"),
                ("quantity", "Количество"),
                ("category", "Категория"),
            ],
            "rows": rows,
            "create_url": "/справочники/продукты/добавить",
            "edit_url_prefix": "/справочники/продукты/изменить/",
            "delete_url_prefix": "/справочники/продукты/удалить/",
            "allow_edit": user.get("role") == "admin",
        },
    )


@router.get("/продукты/добавить", response_class=HTMLResponse)
def products_create_form(request: Request):
    user = require_admin(request)
    return templates.TemplateResponse(
        "admin/edit_product.html",
        {"request": request, "user": user, "title": "Добавить продукт", "action": "/справочники/продукты/добавить", "values": {}},
    )


@router.post("/продукты/добавить", response_class=HTMLResponse)
def products_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    weight: str = Form(""),
    expiry_date: str = Form(""),
    quantity: str = Form(""),
    category: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            INSERT INTO products(name, weight, expiry_date, quantity, category)
            VALUES (:name,
                    NULLIF(:w,'')::numeric,
                    NULLIF(:ed,'')::date,
                    NULLIF(:q,'')::numeric,
                    NULLIF(:cat,''))
            """
        ),
        {"name": name.strip(), "w": weight, "ed": expiry_date, "q": quantity, "cat": category.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/продукты")
    return RedirectResponse(url="/справочники/продукты", status_code=303)


@router.get("/продукты/изменить/{product_id}", response_class=HTMLResponse)
def products_edit_form(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request)
    row = db.execute(
        text("SELECT id, name, weight, expiry_date, quantity, category FROM products WHERE id=:id"),
        {"id": product_id},
    ).mappings().first()

    if not row:
        return render_error(request, "Запись не найдена.", "/справочники/продукты", status_code=404)

    return templates.TemplateResponse(
        "admin/edit_product.html",
        {"request": request, "user": user, "title": "Изменить продукт", "action": f"/справочники/продукты/изменить/{product_id}", "values": row},
    )


@router.post("/продукты/изменить/{product_id}", response_class=HTMLResponse)
def products_edit(
    product_id: int,
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    weight: str = Form(""),
    expiry_date: str = Form(""),
    quantity: str = Form(""),
    category: str = Form(""),
):
    require_admin(request)
    db.execute(
        text(
            """
            UPDATE products
            SET name=:name,
                weight=NULLIF(:w,'')::numeric,
                expiry_date=NULLIF(:ed,'')::date,
                quantity=NULLIF(:q,'')::numeric,
                category=NULLIF(:cat,'')
            WHERE id=:id
            """
        ),
        {"id": product_id, "name": name.strip(), "w": weight, "ed": expiry_date, "q": quantity, "cat": category.strip()},
    )
    err = safe_commit(db)
    if err:
        return render_error(request, err, f"/справочники/продукты/изменить/{product_id}")
    return RedirectResponse(url="/справочники/продукты", status_code=303)


@router.post("/продукты/удалить/{product_id}", response_class=HTMLResponse)
def products_delete(product_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(text("DELETE FROM products WHERE id=:id"), {"id": product_id})
    err = safe_commit(db)
    if err:
        return render_error(request, err, "/справочники/продукты")
    return RedirectResponse(url="/справочники/продукты", status_code=303)
