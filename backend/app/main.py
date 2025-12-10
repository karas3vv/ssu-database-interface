from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .db import engine
from .auth import router as auth_router
from .routers import reference as reference_router
from .routers import orders as orders_router
from .routers import reports as reports_router
from .routers import search as search_router
from .routers import views_input as views_input_router

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Интерфейс ресторана")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(reference_router.router)
app.include_router(orders_router.router)
app.include_router(reports_router.router)
app.include_router(search_router.router)
app.include_router(views_input_router.router)
