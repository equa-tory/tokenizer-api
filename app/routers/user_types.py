# normal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import TicketType
from app.db import get_db
from app.schemas import UserTypesIn

router = APIRouter()

@router.get("/", response_model=UserTypesIn)
def get_valid_types(db: Session = Depends(get_db)):
    return db.query(TicketType).all()