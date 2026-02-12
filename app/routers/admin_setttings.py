import csv
from fastapi import APIRouter, Depends, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Setting

router = APIRouter()


@router.post("/")
async def update_setting(key: str, value: str, db: Session = Depends(get_db)):
    setting = db.get(Setting, key)
    if not setting:
        setting = Setting(key=key, value=value)
    else:
        setting.value = value
    db.add(setting)
    db.commit()
    return {"ok": True}