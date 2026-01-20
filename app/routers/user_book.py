from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import Course, Ticket, TicketType, User
from app.db import get_db
from datetime import datetime
from sqlalchemy import select
from logic import get_user, check_ticket_rules, generate_ticket_number

router = APIRouter()


@router.post("/")
def book_ticket(
    type: str = Query(...),
    timestamp: datetime = Query(...),
    id: int = Query(...),
    tg: int = Query(None),
    db: Session = Depends(get_db)
):
    user = get_user(id=id, tg=tg, db=db)
    check_ticket_rules(user, type, timestamp, db) # TODO: add timestamp checks
    ticket_number = generate_ticket_number(type, db) # TODO: fix number

    ticket_type_obj = db.execute(
        select(TicketType).where(TicketType.name == type)
    ).scalar_one_or_none()

    if not ticket_type_obj:
        raise HTTPException(status_code=404, detail="Тип билета не найден")

    ticket = Ticket(
        name=ticket_number,
        status="active", # TODO: add logic
        ticket_type=ticket_type_obj,
        user_id=user.id,
        timestamp=timestamp
    )

    db.add(ticket)
    if type == db.execute(select(TicketType.name)).scalars().first(): # if "debt"
        user.debt_streak += 1
        db.add(user)
    db.commit()
    db.refresh(ticket)

    return ticket