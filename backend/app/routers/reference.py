from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..db import get_db
from .. import models, schemas
from ..dependencies import require_role, get_current_user

router = APIRouter(prefix="/справочники", tags=["Справочники"])

# === Блюда ===

@router.get("/блюда", response_model=List[schemas.DishOut])
def list_dishes(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Dish).all()

@router.post(
    "/блюда",
    response_model=schemas.DishOut,
    dependencies=[Depends(require_role("admin"))],
)
def create_dish(data: schemas.DishCreate, db: Session = Depends(get_db)):
    dish = models.Dish(**data.dict())
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish

@router.put(
    "/блюда/{dish_id}",
    response_model=schemas.DishOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_dish(dish_id: int, data: schemas.DishCreate, db: Session = Depends(get_db)):
    dish = db.query(models.Dish).get(dish_id)
    if not dish:
        raise HTTPException(404, "Блюдо не найдено")
    for k, v in data.dict().items():
        setattr(dish, k, v)
    db.commit()
    db.refresh(dish)
    return dish

@router.delete(
    "/блюда/{dish_id}",
    dependencies=[Depends(require_role("admin"))],
)
def delete_dish(dish_id: int, db: Session = Depends(get_db)):
    dish = db.query(models.Dish).get(dish_id)
    if not dish:
        raise HTTPException(404, "Блюдо не найдено")
    db.delete(dish)
    db.commit()
    return {"сообщение": "Удалено"}


# === Столы ===

@router.get("/столы", response_model=List[schemas.TableOut])
def list_tables(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Table).all()

@router.post(
    "/столы",
    response_model=schemas.TableOut,
    dependencies=[Depends(require_role("admin"))],
)
def create_table(data: schemas.TableCreate, db: Session = Depends(get_db)):
    table = models.Table(**data.dict())
    db.add(table)
    db.commit()
    db.refresh(table)
    return table

@router.put(
    "/столы/{table_id}",
    response_model=schemas.TableOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_table(table_id: int, data: schemas.TableCreate, db: Session = Depends(get_db)):
    table = db.query(models.Table).get(table_id)
    if not table:
        raise HTTPException(404, "Стол не найден")
    for k, v in data.dict().items():
        setattr(table, k, v)
    db.commit()
    db.refresh(table)
    return table

@router.delete(
    "/столы/{table_id}",
    dependencies=[Depends(require_role("admin"))],
)
def delete_table(table_id: int, db: Session = Depends(get_db)):
    table = db.query(models.Table).get(table_id)
    if not table:
        raise HTTPException(404, "Стол не найден")
    db.delete(table)
    db.commit()
    return {"сообщение": "Удалено"}


# === Официанты ===

@router.get("/официанты", response_model=List[schemas.WaiterOut])
def list_waiters(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Waiter).all()

@router.post(
    "/официанты",
    response_model=schemas.WaiterOut,
    dependencies=[Depends(require_role("admin"))],
)
def create_waiter(data: schemas.WaiterCreate, db: Session = Depends(get_db)):
    waiter = models.Waiter(**data.dict())
    db.add(waiter)
    db.commit()
    db.refresh(waiter)
    return waiter

@router.put(
    "/официанты/{waiter_id}",
    response_model=schemas.WaiterOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_waiter(waiter_id: int, data: schemas.WaiterCreate, db: Session = Depends(get_db)):
    waiter = db.query(models.Waiter).get(waiter_id)
    if not waiter:
        raise HTTPException(404, "Официант не найден")
    for k, v in data.dict().items():
        setattr(waiter, k, v)
    db.commit()
    db.refresh(waiter)
    return waiter

@router.delete(
    "/официанты/{waiter_id}",
    dependencies=[Depends(require_role("admin"))],
)
def delete_waiter(waiter_id: int, db: Session = Depends(get_db)):
    waiter = db.query(models.Waiter).get(waiter_id)
    if not waiter:
        raise HTTPException(404, "Официант не найден")
    db.delete(waiter)
    db.commit()
    return {"сообщение": "Удалено"}


# === Гости ===

@router.get("/гости", response_model=List[schemas.GuestOut])
def list_guests(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.Guest).all()

@router.post(
    "/гости",
    response_model=schemas.GuestOut,
    dependencies=[Depends(require_role("admin"))],
)
def create_guest(data: schemas.GuestCreate, db: Session = Depends(get_db)):
    guest = models.Guest(**data.dict())
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest

@router.put(
    "/гости/{guest_id}",
    response_model=schemas.GuestOut,
    dependencies=[Depends(require_role("admin"))],
)
def update_guest(guest_id: int, data: schemas.GuestCreate, db: Session = Depends(get_db)):
    guest = db.query(models.Guest).get(guest_id)
    if not guest:
        raise HTTPException(404, "Гость не найден")
    for k, v in data.dict().items():
        setattr(guest, k, v)
    db.commit()
    db.refresh(guest)
    return guest

@router.delete(
    "/гости/{guest_id}",
    dependencies=[Depends(require_role("admin"))],
)
def delete_guest(guest_id: int, db: Session = Depends(get_db)):
    guest = db.query(models.Guest).get(guest_id)
    if not guest:
        raise HTTPException(404, "Гость не найден")
    db.delete(guest)
    db.commit()
    return {"сообщение": "Удалено"}