from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.db import get_db
from app.models import Ticket, TicketType
from logic import get_user, check_ticket_rules, generate_ticket_number
from app.schemas import UserBookIn


router = APIRouter()


@router.post("/", response_model=UserBookIn)
def book_ticket(
    type: str,
    id: Optional[int] = None,
    tg_id: Optional[int] = None,
    timestamp: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    if not id and not tg_id:
        raise HTTPException(status_code=400, detail="Provide ?id= or ?tg=")

    user = get_user(id=id, tg_id=tg_id, db=db)
    check_ticket_rules(user, type, timestamp, db)
    ticket_number = generate_ticket_number(type, db)

    ticket_type_obj = db.execute(
        select(TicketType).where(TicketType.name == type)
    ).scalar_one_or_none()

    if not ticket_type_obj:
        raise HTTPException(status_code=404, detail="Ticket type not found")

    ticket = Ticket(
        name=ticket_number,
        status="active", # TODO: add logic
        ticket_type_id=ticket_type_obj.id,
        user_id=user.id,
        timestamp=timestamp if ticket_type_obj.require_time else None,
    )

    db.add(ticket)
    if type == db.execute(select(TicketType.name)).scalars().first(): # if "debt"
        user.debt_streak += 1
        db.add(user)
    db.commit()
    db.refresh(ticket)

    return ticket