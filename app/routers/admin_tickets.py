from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from app.models import *
from app.db import get_db
from app.schemas import AdminTicketIn

router = APIRouter()

@router.post("/")
def upsert_ticket(
    id: Optional[int] = None,
    name: Optional[str] = None,
    number: Optional[int] = None,
    status: Optional[str] = None,
    timestamp: Optional[datetime] = None,
    user_id: Optional[int] = None,
    ticket_type_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    # --- UPDATE ---
    if id is not None:
        ticket = db.query(Ticket).filter(Ticket.id == id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if name is not None:
            ticket.name = name
        if number is not None:
            ticket.number = number
        if status is not None:
            ticket.status = status
        if timestamp is not None:
            ticket.timestamp = timestamp
        if user_id is not None:
            ticket.user_id = user_id
        if ticket_type_id is not None:
            ticket.ticket_type_id = ticket_type_id

        db.commit()
        db.refresh(ticket)
        return {"mode": "updated", "ticket": ticket}

    # --- CREATE ---
    # if not ticket_type_id:
    #     raise HTTPException(status_code=400, detail="type id is required for creation")
    
    if not number: # get last +1
        last_number = db.execute(
            select(func.max(Ticket.number))
        ).scalar() or 0

        number = last_number + 1

    if not name:
        # make prefix based on related ticket_type title first letter
        prefix = db.execute(
            select(TicketType.symbol).where(TicketType.id == ticket_type_id)
        ).scalar_one_or_none()

        name = f"{prefix}-{str(number).zfill(4)}"

    ticket = Ticket(
        name=name,
        number=number,
        status=status,
        timestamp=timestamp,
        user_id=user_id,
        ticket_type_id=ticket_type_id,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {"mode": "created", "ticket": ticket}