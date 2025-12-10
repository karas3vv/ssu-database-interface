from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List

from ..db import get_db
from ..dependencies import get_current_user
from .. import schemas

router = APIRouter(prefix="/отчёты", tags=["Отчёты"])

@router.get("/выручка")
def get_revenue(date_from: str, date_to: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = db.execute(
        text("SELECT get_revenue(:df, :dt)"),
        {"df": date_from, "dt": date_to},
    ).scalar()
    return {"выручка": float(row) if row is not None else 0.0}

@router.get("/продажи_блюд", response_model=List[schemas.DishSalesRow])
def dishes_sales(db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.execute(text("SELECT * FROM dishes_sales()")).all()
    return [
        schemas.DishSalesRow(
            dish_name=r[0],
            total_sold=r[1],
            total_revenue=float(r[2]),
            avg_price=float(r[3]),
        )
        for r in rows
    ]

@router.get("/статистика_гостей", response_model=List[schemas.GuestStatsRow])
def guest_statistics(limit: int = 10, db: Session = Depends(get_db), user=Depends(get_current_user)):
    rows = db.execute(text("SELECT * FROM guest_statistics(:lim)"), {"lim": limit}).all()
    return [
        schemas.GuestStatsRow(
            guest_id=r[0],
            full_name=r[1],
            total_orders=r[2],
            total_revenue=float(r[3]),
            avg_check=float(r[4]),
        )
        for r in rows
    ]
