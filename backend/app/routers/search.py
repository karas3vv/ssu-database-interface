from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..db import get_db
from ..dependencies import get_current_user

router = APIRouter(prefix="/поиск", tags=["Поиск"])

@router.get("/заказы_по_клиенту")
def search_orders(
    гость: str | None = None,
    блюдо: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    sql = """
    SELECT o.id, g.last_name || ' ' || g.first_name AS guest_name,
           o.order_time, o.total_amount
    FROM orders o
    JOIN guests g ON g.id = o.guest_id
    LEFT JOIN order_items oi ON oi.order_id = o.id
    LEFT JOIN dishes d ON d.id = oi.dish_id
    WHERE (:guest IS NULL OR g.last_name ILIKE '%' || :guest || '%')
      AND (:dish IS NULL OR d.name ILIKE '%' || :dish || '%')
    GROUP BY o.id, guest_name, o.order_time, o.total_amount
    ORDER BY o.order_time;
    """
    rows = db.execute(text(sql), {"guest": гость, "dish": блюдо}).all()
    return [
        {
            "id_заказа": r[0],
            "гость": r[1],
            "время": r[2],
            "сумма": float(r[3]) if r[3] is not None else None,
        }
        for r in rows
    ]
