from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import Course, Ticket, TicketType, User
from app.db import get_db
from datetime import datetime
from sqlalchemy import select

from models import *
from db import engine



def get_user(id: int = None, tg: int = None, db: Session = Depends(get_db)):
    if not id and not tg:
        raise HTTPException(status_code=400, detail="Provide ?id= or ?tg=")
    if tg:
        user = db.execute(select(User).where(User.tg_id == tg)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="TG User not found")

    else:
        user = db.get(User, id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    return user



def check_ticket_rules(user: User, ticket_type: str, timestamp: datetime | None, db: Session):
    tt = db.execute(
        select(TicketType).where(TicketType.name == ticket_type)
    ).scalar_one_or_none()

    if not tt:
        raise HTTPException(status_code=400, detail="Wrong ticket type")

    # --- timestamp check logic ---
    # TODO:
    # 1. check if timestamp is taken
    # 2. check if timestamp is in the future
    # 3. check if timestamp is in right dates and time slots

    # --- cooldown logic ---
    if ticket_type == db.execute(select(TicketType.name)).scalars().first():
        # get last ticket and check if 10 minutes have passed
        last_ticket = db.execute( # TODO: think if it should be only debt or for all types cooldown
            select(Ticket)
            .order_by(Ticket.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_ticket and last_ticket.ticket_type.name == ticket_type: # example cooldown for same type: last_ticket.type == ticket_type: --- IGNORE ---
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            cooldown = 10  # minutes # TODO: config cooldown
            if last_ticket.created_at and (now - last_ticket.created_at) < timedelta(minutes=cooldown):
                raise HTTPException(
                    status_code=400,
                    detail=f"Wait at least {cooldown} minutes between issuing tickets of the same type"
                )



    # --- require_time logic ---
    if tt.require_time and tt.require_time > 0:
        if not timestamp:
            raise HTTPException(status_code=400, detail="This ticket type requires a timestamp")

        # timestamp uniqueness (global)
        exists = db.execute(
            select(Ticket.id).where(Ticket.timestamp == timestamp)
        ).scalar_one_or_none()
        if exists:
            raise HTTPException(status_code=400, detail="Timestamp already taken")
    else:
        # timestamp must be ignored completely
        timestamp = None

    # --- max_per_user logic ---
    user_tickets_of_type = db.execute(
        select(Ticket)
        .where(
            Ticket.user_id == user.id,
            Ticket.ticket_type_id == tt.id,
            Ticket.status == "active",
        )
    ).scalars().all()

    if tt.max_per_user is not None and len(user_tickets_of_type) >= tt.max_per_user:
        raise HTTPException(
            status_code=400,
            detail="User has reached the maximum number of active tickets of this type"
        )

    # --- debt-specific logic (kept but simplified) ---
    if tt.name == "debt":
        last_debt_user_id = db.execute(
            select(Ticket.user_id)
            .where(Ticket.ticket_type_id == tt.id)
            .order_by(Ticket.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_debt_user_id == user.id and user.debt_streak >= 2:
            raise HTTPException(
                status_code=400,
                detail="Cannot take debt more than twice in a row"
            )

        # reset streaks for others
        others = db.execute(
            select(User).where(User.id != user.id, User.debt_streak >= 2)
        ).scalars().all()

        for u in others:
            u.debt_streak = 0
            db.add(u)

def generate_ticket_number(ticket_type: str, db: Session):
    prefix = db.execute(select(TicketType.symbol).where(TicketType.name == ticket_type)).scalar_one_or_none()

    last_ticket = db.execute(
        select(Ticket)
        # .where(Ticket.name.like(f"{prefix}-%"))
        .order_by(Ticket.name.desc())
        .limit(1)
    ).scalar_one_or_none()

    last_number = int(last_ticket.name.split("-")[1]) if last_ticket else 0
    return f"{prefix}-{str(last_number + 1).zfill(4)}"
