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

    # Return plain dicts so the desktop Manager can show who booked the ticket
    # ("user" = name, or null when unknown — e.g. tickets created from ButtonsApp).
    return [
        {
            "id": t.id,
            "number": t.number,
            "name": t.name,
            "status": t.status,
            "timestamp": t.timestamp.isoformat() if t.timestamp else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "user_id": t.user_id,
            "user": t.user.name if t.user else None,
            "ticket_type_id": t.ticket_type_id,
        }
        for t in tickets
    ]
