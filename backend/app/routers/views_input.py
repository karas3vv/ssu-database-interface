from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import get_db
from ..dependencies import get_current_user, require_role

router = APIRouter(prefix="/представления", tags=["Ввод через представления"])

# Пример: гости через v_adult_guests (гости старше 25 лет)

@router.get("/взрослые_гости")
def list_adult_guests(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.execute(text("SELECT * FROM v_adult_guests")).all()
    result = []
    for r in rows:
        result.append(
            {
                "id": r.id,
                "фамилия": r.last_name,
                "имя": r.first_name,
                "отчество": r.middle_name,
                "дата_рождения": r.birth_date,
            }
        )
    return result

@router.post(
    "/взрослые_гости",
    dependencies=[Depends(require_role("admin"))],
)
def insert_adult_guest(
    last_name: str,
    first_name: str,
    birth_date: str,
    db: Session = Depends(get_db),
):
    db.execute(
        text(
            "INSERT INTO v_adult_guests_local (last_name, first_name, birth_date) "
            "VALUES (:ln, :fn, :bd)"
        ),
        {"ln": last_name, "fn": first_name, "bd": birth_date},
    )
    db.commit()
    return {"сообщение": "Гость добавлен через представление"}
