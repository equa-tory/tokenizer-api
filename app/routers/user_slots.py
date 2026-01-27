# normal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from logic import get_timeslots

router = APIRouter()

@router.get("/")
def get_slots(db: Session = Depends(get_db)):
    return {"timeslots": get_timeslots(db)}