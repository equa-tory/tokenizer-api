from fastapi import FastAPI
from app.models import *

from app.routers import (
    admin_all,
    admin_users,
    admin_courses,
    admin_types,
    admin_delete,
    admin_reset,
    admin_tickets,

    user_dates,
    user_slots,
    user_book,
    user_cancel,
    user_status,
    user_types,
)

app = FastAPI(title="Tokenizer-API")


@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    from app.db import ensure_default_tickettypes, SessionLocal
    ensure_default_tickettypes(SessionLocal())


app.include_router(admin_all.router, prefix="/all", tags=["admin"])
app.include_router(admin_types.router, prefix="/ticket/types", tags=["admin"])
app.include_router(admin_tickets.router, prefix="/ticket", tags=["admin"])
#app.include_router(admin_courses.router, prefix="/courses", tags=["admin"])
app.include_router(admin_users.router, prefix="/users", tags=["admin"])
app.include_router(admin_delete.router, prefix="/delete", tags=["admin"])
app.include_router(admin_reset.router, prefix="/reset-db", tags=["admin"])

app.include_router(user_types.router, prefix="/ticket/types", tags=["user"])
app.include_router(user_book.router, prefix="/ticket/book", tags=["user"])
app.include_router(user_cancel.router, prefix="/ticket/cancel", tags=["user"])
# app.include_router(user_dates.router, prefix="/get_days", tags=["user"])
app.include_router(user_slots.router, prefix="/timeslots", tags=["user"])
app.include_router(user_status.router, prefix="/status", tags=["user"])
