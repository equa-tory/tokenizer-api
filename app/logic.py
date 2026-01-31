from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import Course, Ticket, TicketType, User
from app.db import get_db
import datetime
from datetime import datetime, timedelta, time as dt_time
from sqlalchemy import select
from sqlalchemy import and_
from datetime import datetime, timedelta

from models import *
from db import engine



# ----------------------------

START_TIME = dt_time(16, 0)
END_TIME = dt_time(18, 0)
SLOT_INTERVAL = 10  # minutes
DEBT_WEEKDAY = 4 # friday
DEBT_COOLDOWN = 15  # minutes

# ----------------------------




def get_user(id: int = None, tg_id: int = None, db: Session = Depends(get_db)):
    if not id and not tg_id:
        raise HTTPException(status_code=400, detail="Provide ?id= or ?tg=")
    if tg_id:
        user = db.execute(select(User).where(User.tg_id == tg_id)).scalar_one_or_none()
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
    from datetime import datetime, timedelta # TODO: wtf

    if timestamp:
        now = datetime.utcnow()

        # 1. только будущее
        if timestamp <= now:
            raise HTTPException(status_code=400, detail="Timestamp must be in the future")

        # 2. проверка даты (должна быть в ближайшую или следующую пятницу)
        today = now.date()
        days_ahead = (DEBT_WEEKDAY - today.weekday()) % 7
        if days_ahead == 0 and now.time() >= START_TIME:
            days_ahead = 7
        first_friday = today + timedelta(days=days_ahead)
        second_friday = first_friday + timedelta(days=7)
        if timestamp.date() not in [first_friday, second_friday]:
            raise HTTPException(status_code=400, detail="Timestamp date must be on allowed days")

        # 3. проверка времени дня
        if not (START_TIME <= timestamp.time() < END_TIME):
            raise HTTPException(status_code=400, detail="Timestamp out of allowed time range")

        # 4. проверка кратности слоту
        if timestamp.minute % SLOT_INTERVAL != 0 or timestamp.second != 0:
            raise HTTPException(status_code=400, detail="Timestamp is not aligned with slot interval")

        # 5. слот не занят (через БД)   
        taken = db.execute(
            select(Ticket.id).where(
                and_(
                    Ticket.timestamp == timestamp,
                    Ticket.status == "active"
                )
            )
        ).scalar_one_or_none()

        if taken:
            raise HTTPException(status_code=400, detail="This time slot is already taken")


    # --- cooldown logic ---
    if ticket_type == db.execute(select(TicketType.name)).scalars().first():
        # get last ticket and check if N minutes have passed
        last_ticket = db.execute(
            select(Ticket)
            .order_by(Ticket.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_ticket and last_ticket.ticket_type.name == ticket_type: # example cooldown for same type: last_ticket.type == ticket_type: --- IGNORE ---
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            cooldown = DEBT_COOLDOWN
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




# if need only timeslots
# def get_timeslots(date: str, db: Session):
#     query_date = datetime.strptime(date, "%Y-%m-%d").date()
#     start_time = datetime.combine(query_date, START_TIME)
#     end_time = datetime.combine(query_date, END_TIME)
#     slots = []
#     current = start_time
#     while current < end_time:
#         taken = db.query(Ticket).filter(Ticket.timestamp == current).first()
#         slots.append({"time": current.time().strftime("%H:%M"), "available": not bool(taken)})
#         current += timedelta(minutes=SLOT_INTERVAL)
#     return slots

def get_timeslots(db: Session):
    today = datetime.now().date()

    # вычисляем ближайшую и следующую пятницу (как в get_days)
    days_ahead = (DEBT_WEEKDAY - today.weekday()) % 7
    if days_ahead == 0 and datetime.now().time() >= START_TIME:
        days_ahead = 7

    dates = [
        today + timedelta(days=days_ahead),
        today + timedelta(days=days_ahead + 7),
    ]

    result = []

    for d in dates:
        start_time = datetime.combine(d, START_TIME)
        end_time = datetime.combine(d, END_TIME)

        slots = []
        current = start_time
        while current < end_time:
            taken = db.execute(
                select(Ticket.id).where(Ticket.timestamp == current)
            ).scalar_one_or_none()

            slots.append({
                "time": current.time().strftime("%H:%M"),
                "available": not bool(taken),
            })

            current += timedelta(minutes=SLOT_INTERVAL)

        result.append({
            "date": d.isoformat(),
            "slots": slots,
        })

    return result
