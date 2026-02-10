import time
import json

from app.db import SessionLocal
from fastapi import FastAPI
from app.models import *
from app.logic import safe_json

from app.routers import (
    admin_all,
    admin_users,
    admin_courses,
    admin_types,
    admin_delete,
    admin_reset,
    admin_tickets,
    admin_logs,
    admin_export,
    admin_import,

    user_dates,
    user_slots,
    user_book,
    user_cancel,
    user_status,
    user_types,
)

app = FastAPI(title="Tokenizer-API")


#region --- Init ---
@app.on_event("startup")
async def startup_event():
    print("Starting up...")
    from app.db import ensure_default_tickettypes, SessionLocal
    ensure_default_tickettypes(SessionLocal())

@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()

    body = await request.body()
    response = await call_next(request)

    duration = time.time() - start

    log = Log(
        kind="http",
        action=f"{request.method} {request.url.path}",
        status_code=response.status_code,
        # user_id=extract_user(request),
        data={
            "query": dict(request.query_params),
            "body": safe_json(body),
            "duration_ms": int(duration * 1000),
        },
    )
    db = SessionLocal()
    db.add(log)
    db.commit()
    db.close()
    return response
#endregion --- --- ---


app.include_router(admin_all.router, prefix="/all", tags=["_admin", "etc"])
app.include_router(admin_types.router, prefix="/ticket/types", tags=["_admin", "ticket"])
app.include_router(admin_tickets.router, prefix="/ticket", tags=["_admin", "ticket"])
#app.include_router(admin_courses.router, prefix="/courses", tags=["_admin"])
app.include_router(admin_users.router, prefix="/users", tags=["_admin", "users"])
app.include_router(admin_delete.router, prefix="/delete", tags=["_admin", "etc"])
app.include_router(admin_reset.router, prefix="/reset-db", tags=["_admin", "etc"])
app.include_router(admin_logs.router, prefix="/logs", tags=["_admin", "etc"])
app.include_router(admin_export.router, prefix="/users/export", tags=["_admin", "users"])
app.include_router(admin_import.router, prefix="/users/import", tags=["_admin", "users"])

app.include_router(user_types.router, prefix="/ticket/types", tags=["_user", "ticket"])
app.include_router(user_book.router, prefix="/ticket/book", tags=["_user", "ticket"])
app.include_router(user_cancel.router, prefix="/ticket/cancel", tags=["_user", "ticket"])
# app.include_router(user_dates.router, prefix="/get_days", tags=["_user"])
app.include_router(user_slots.router, prefix="/timeslots", tags=["_user", "etc"])
app.include_router(user_status.router, prefix="/status", tags=["_user", "etc"])
