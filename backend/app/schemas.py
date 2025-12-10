from datetime import date, datetime, time
from pydantic import BaseModel
from typing import Optional, List


# === Пользователи / токены ===

class UserBase(BaseModel):
    login: str
    role: str

class UserCreate(BaseModel):
    login: str
    password: str
    role: str

class UserOut(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None


# === Справочники ===

class SupplierBase(BaseModel):
    name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierOut(SupplierBase):
    id: int
    class Config:
        from_attributes = True


class DishBase(BaseModel):
    name: str
    category: Optional[str] = None
    price: float
    country_of_origin: Optional[str] = None

class DishCreate(DishBase):
    pass

class DishOut(DishBase):
    id: int
    class Config:
        from_attributes = True


class TableBase(BaseModel):
    table_number: int
    seats: int
    status: Optional[str] = None

class TableCreate(TableBase):
    pass

class TableOut(TableBase):
    id: int
    class Config:
        from_attributes = True


class WaiterBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    salary: Optional[float] = None

class WaiterCreate(WaiterBase):
    pass

class WaiterOut(WaiterBase):
    id: int
    class Config:
        from_attributes = True


class GuestBase(BaseModel):
    last_name: str
    first_name: str
    middle_name: Optional[str] = None
    birth_date: Optional[date] = None

class GuestCreate(GuestBase):
    pass

class GuestOut(GuestBase):
    id: int
    total_orders: Optional[float] = None
    total_discount: Optional[float] = None
    class Config:
        from_attributes = True


# === Заказы ===

class OrderItemBase(BaseModel):
    dish_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemOut(OrderItemBase):
    order_id: int
    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    guest_id: int
    table_id: Optional[int] = None
    waiter_id: Optional[int] = None
    order_time: Optional[datetime] = None
    status: Optional[str] = None

class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = []

class OrderOut(OrderBase):
    id: int
    total_amount: Optional[float] = None
    items: List[OrderItemOut] = []
    class Config:
        from_attributes = True


# === Примеры выходных схем для отчётов ===

class DishSalesRow(BaseModel):
    dish_name: str
    total_sold: int
    total_revenue: float
    avg_price: float

class GuestStatsRow(BaseModel):
    guest_id: int
    full_name: str
    total_orders: int
    total_revenue: float
    avg_check: float
