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
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": None},
    )


@router.post("/вход")
def login(
    request: Request,
    db: Session = Depends(get_db),
    login: str = Form(...),
    password: str = Form(...),
):
    row = db.execute(
        text("SELECT id, login, password_hash, role FROM users WHERE login = :login"),
        {"login": login},
    ).mappings().first()

    if row is None or password != row["password_hash"]:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Неверный логин или пароль."},
            status_code=400,
        )

    request.session["user"] = {
        "id": row["id"],
        "login": row["login"],
        "role": row["role"],
    }

    return RedirectResponse(url="/", status_code=303)


@router.post("/выход")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
