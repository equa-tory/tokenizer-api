from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import *
from app.db import get_db

router = APIRouter()

@router.post("/")
def upsert_ticket(
    id: Optional[int] = None,
    name: Optional[str] = None,
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
    if not name or not status:
        raise HTTPException(status_code=400, detail="name and status are required for create")

    ticket = Ticket(
        name=name,
        status=status,
        timestamp=timestamp,
        user_id=user_id,
        ticket_type_id=ticket_type_id,
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return {"mode": "created", "ticket": ticket}