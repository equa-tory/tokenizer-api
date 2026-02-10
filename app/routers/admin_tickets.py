from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, func
from app.models import *
from app.db import get_db
from app.schemas import AdminTicketIn
from app.logic import generate_ticket_number

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
    _name, _number = generate_ticket_number(db=db, last_number=number)
    if not name:
        name = _name
    if not number:
        number = _number

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