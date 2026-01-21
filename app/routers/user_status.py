from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import Course, Ticket, TicketType, User
from app.db import get_db
from datetime import datetime
from sqlalchemy import select
from logic import get_user

router = APIRouter()


@router.get("/")
def status(
    id: int = Query(None),
    db: Session = Depends(get_db),
):
    user = get_user(id=id, db=db)

    # ---- Get tickets ----
    tickets = db.execute(
        select(Ticket).where(Ticket.user_id == user.id)
    ).scalars().all()
    if not tickets:
        raise HTTPException(status_code=404, detail="User has no tickets")

    # ---- Last queued ticket ----
    last_ticket = db.execute(
        select(Ticket)
        .order_by(Ticket.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    return {
        "user": user,
        "tickets": tickets,
        "last_ticket": last_ticket,
    }