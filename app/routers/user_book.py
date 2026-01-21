from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import Course, Ticket, TicketType, User
from typing import Optional
from app.db import get_db
from datetime import datetime
from sqlalchemy import select
from logic import get_user, check_ticket_rules, generate_ticket_number

router = APIRouter()


@router.post("/")
def book_ticket(
    type: str = Query(...),
    timestamp: Optional[datetime] = None,
    id: int = Query(...),
    tg: int = Query(None),
    db: Session = Depends(get_db)
):
    user = get_user(id=id, tg=tg, db=db)
    check_ticket_rules(user, type, timestamp, db)
    ticket_number = generate_ticket_number(type, db)

    ticket_type_obj = db.execute(
        select(TicketType).where(TicketType.name == type)
    ).scalar_one_or_none()

    if not ticket_type_obj:
        raise HTTPException(status_code=404, detail="Тип билета не найден")

    ticket = Ticket(
        name=ticket_number,
        status="active",
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