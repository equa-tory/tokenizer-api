from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import Course, Ticket, TicketType, User
from app.db import get_db
from datetime import datetime
from sqlalchemy import select
from logic import get_user
from app.schemas import UserStatusIn

router = APIRouter()


@router.get("/")
def status(
    db: Session = Depends(get_db),
):
    # ---- Get tickets ----
    tickets = db.execute(
        select(Ticket).order_by(Ticket.created_at.asc())
    ).scalars().all()


    return tickets