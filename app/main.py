from fastapi import FastAPI
from app.models import *

from app.routers import (
    admin_all,
    admin_users,
    admin_courses,
    admin_types,

    user_courses,
    user_dates,
    user_slots,
)

app = FastAPI(title="Tokenizer-API")

app.include_router(admin_all.router, prefix="/all", tags=["admin"])
app.include_router(admin_types.router, prefix="/tickettypes", tags=["admin"])
app.include_router(admin_courses.router, prefix="/courses", tags=["admin"])
app.include_router(admin_users.router, prefix="/users", tags=["admin"])

app.include_router(user_courses.router, prefix="/get_valid_types", tags=["user"])
app.include_router(user_dates.router, prefix="/get_days", tags=["user"])
app.include_router(user_slots.router, prefix="/get_timeslots", tags=["user"])
