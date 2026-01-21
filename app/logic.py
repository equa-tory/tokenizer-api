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
            raise HTTPException(status_code=404, detail="TG Пользователь не найден")

    else:
        user = db.get(User, id)
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user



def check_ticket_rules(user: User, ticket_type: str, timestamp: datetime | None, db: Session):
    tt = db.execute(
        select(TicketType).where(TicketType.name == ticket_type)
    ).scalar_one_or_none()

    if not tt:
        raise HTTPException(status_code=400, detail="Неверный тип билета")

    # --- timestamp check logic ---
    # TODO:
    # 1. check if timestamp is taken
    # 2. check if timestamp is in the future
    # 3. check if timestamp is in right dates and time slots

    # get last ticket and check if 10 minutes have passed
    last_ticket = db.execute(
        select(Ticket)
        .order_by(Ticket.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if last_ticket:
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        cooldown = 10  # minutes # TODO: config cooldown
        if last_ticket.timestamp and (now - last_ticket.timestamp) < timedelta(minutes=cooldown):
            raise HTTPException(
                status_code=400,
                detail=f"Подождите минимум {cooldown} минут перед созданием нового билета"
            )



    # --- require_time logic ---
    if tt.require_time and tt.require_time > 0:
        if not timestamp:
            raise HTTPException(status_code=400, detail="Для этого типа билета требуется время")

        # timestamp uniqueness (global)
        exists = db.execute(
            select(Ticket.id).where(Ticket.timestamp == timestamp)
        ).scalar_one_or_none()
        if exists:
            raise HTTPException(status_code=400, detail="Это время уже занято")
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
            detail="Достигнут лимит билетов этого типа"
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
                detail="Нельзя брать задолженность более двух раз подряд"
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
