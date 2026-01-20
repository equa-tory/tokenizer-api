from http.client import HTTPException
from app.db import engine, SessionLocal, ensure_default_tickettypes
from app.models import Base
from fastapi import Header, APIRouter

router = APIRouter()

@router.post("/")
def reset_db(
    # confirm: bool = False,
    # x_admin_token: str | None = Header(default=None),
):
    # простая защита от случайного вызова
    # if not confirm:
    #     raise HTTPException(
    #         status_code=400,
    #         detail="confirm=true required"
    #     )

    # if x_admin_token != "DEV_RESET_TOKEN":
    #     raise HTTPException(
    #         status_code=403,
    #         detail="Invalid admin token"
    #     )

    # полный reset
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # seed defaults
    db = SessionLocal()
    try:
        ensure_default_tickettypes(db)
        db.commit()
    finally:
        db.close()

    return {"status": "ok", "message": "Database recreated"}