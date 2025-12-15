from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import get_db

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/вход", response_class=HTMLResponse)
def login_form(request: Request):
    next_url = request.query_params.get("next", "/")
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None, "next": next_url},
    )


@router.post("/вход")
def login(
    request: Request,
    db: Session = Depends(get_db),
    login: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
):
    # безопасно: редиректим только на внутренние пути
    if not next.startswith("/"):
        next = "/"

    row = db.execute(
        text("SELECT id, login, password_hash, role, guest_id FROM users WHERE login = :login"),
        {"login": login},
    ).mappings().first()

    if row is None or password != row["password_hash"]:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль.", "next": next},
            status_code=400,
        )

    user_id = row["id"]
    guest_id = row["guest_id"]

    # Автопривязка: если guest_id ещё не задан — создаём guests и привязываем
    if guest_id is None:
        new_guest = db.execute(
            text("""
                INSERT INTO guests (last_name, first_name)
                VALUES (:last_name, :first_name)
                RETURNING id
            """),
            {"last_name": row["login"], "first_name": "Пользователь"},
        ).mappings().first()

        guest_id = new_guest["id"]

        db.execute(
            text("UPDATE users SET guest_id = :guest_id WHERE id = :uid"),
            {"guest_id": guest_id, "uid": user_id},
        )
        db.commit()

    request.session["user"] = {
        "id": user_id,
        "login": row["login"],
        "role": row["role"],
        "guest_id": guest_id,
    }

    return RedirectResponse(url=next, status_code=303)


@router.post("/выход")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
