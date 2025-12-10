from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from typing import List

from ..db import get_db
from .. import models, schemas
from ..dependencies import get_current_user

router = APIRouter(prefix="/заказы", tags=["Заказы"])

@router.get("/", response_model=List[schemas.OrderOut])
def list_orders(db: Session = Depends(get_db), user=Depends(get_current_user)):
    orders = db.query(models.Order).all()
    return orders

@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(models.Order).get(order_id)
    if not order:
        raise HTTPException(404, "Заказ не найден")
    return order

@router.post("/", response_model=schemas.OrderOut)
def create_order(data: schemas.OrderCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = models.Order(
        guest_id=data.guest_id,
        table_id=data.table_id,
        waiter_id=data.waiter_id,
        order_time=data.order_time,
        status=data.status,
    )
    db.add(order)
    db.flush()

    for item in data.items:
        oi = models.OrderItem(
            order_id=order.id,
            dish_id=item.dish_id,
            quantity=item.quantity,
        )
        db.add(oi)

    db.commit()
    db.refresh(order)
    return order
