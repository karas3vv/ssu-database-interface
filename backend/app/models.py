from sqlalchemy import Column, Integer, String, Text, Numeric, Date, Time, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# === Пользователи ===

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # 'admin' или 'user'


# === Таблицы из твоей схемы (сокращённо, только то, что нужно для интерфейса) ===

class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    address = Column(Text)
    contact_person = Column(Text)
    phone = Column(Text)
    email = Column(Text)


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    weight = Column(Numeric)
    expiry_date = Column(Date)
    quantity = Column(Numeric)
    category = Column(Text)


class Dish(Base):
    __tablename__ = "dishes"
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    category = Column(Text)
    price = Column(Numeric, nullable=False)
    country_of_origin = Column(Text)


class Table(Base):
    __tablename__ = "tables"
    id = Column(Integer, primary_key=True)
    table_number = Column(Integer, nullable=False)
    seats = Column(Integer, nullable=False)
    status = Column(Text)


class Waiter(Base):
    __tablename__ = "waiters"
    id = Column(Integer, primary_key=True)
    last_name = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    middle_name = Column(Text)
    salary = Column(Numeric)


class Guest(Base):
    __tablename__ = "guests"
    id = Column(Integer, primary_key=True)
    last_name = Column(Text, nullable=False)
    first_name = Column(Text, nullable=False)
    middle_name = Column(Text)
    birth_date = Column(Date)
    total_orders = Column(Numeric)
    total_discount = Column(Numeric)


class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey("tables.id"))
    guest_id = Column(Integer, ForeignKey("guests.id"))
    booking_date = Column(Date, nullable=False)
    guests_count = Column(Integer)
    booking_start = Column(Time)
    booking_end = Column(Time)


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    table_id = Column(Integer, ForeignKey("tables.id"))
    waiter_id = Column(Integer, ForeignKey("waiters.id"))
    order_time = Column(DateTime)
    total_amount = Column(Numeric)
    status = Column(Text)
    booking_id = Column(Integer, ForeignKey("bookings.id"))

    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"
    order_id = Column(Integer, ForeignKey("orders.id"), primary_key=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), primary_key=True)
    quantity = Column(Integer)

    order = relationship("Order", back_populates="items")
    dish = relationship("Dish")
