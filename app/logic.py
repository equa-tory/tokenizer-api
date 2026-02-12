import json

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Ticket, TicketType, User
from app.db import get_db
import datetime
from datetime import datetime, timedelta, time as dt_time
from sqlalchemy import select, and_
from datetime import datetime, timedelta

from models import *

# ----------------------------

#region SETTINGS
from dataclasses import dataclass

@dataclass
class AppSettings:
    DEBT_WEEKDAY: int
    START_TIME: dt_time
    END_TIME: dt_time
    SLOT_INTERVAL: int
    DEBT_COOLDOWN: int
    MAX_TICKETS: int
    MAX_SLOT_GAP: int
    MAX_SLOT_SEQUENCE: int
    MAX_USER_DEBT_STREAK: int
    MAX_LOGS: int

def get_setting(db: Session, key: str, cast_type=str):
    setting = db.get(Setting, key)
    if not setting:
        raise Exception(f"Setting {key} not found")
    return cast_type(setting.value)

def load_settings(db: Session) -> AppSettings:
    return AppSettings(
        DEBT_WEEKDAY=get_setting(db, "DEBT_WEEKDAY", int),
        START_TIME=datetime.strptime(
            get_setting(db, "START_TIME", str), "%H:%M"
        ).time(),
        END_TIME=datetime.strptime(
            get_setting(db, "END_TIME", str), "%H:%M"
        ).time(),
        SLOT_INTERVAL=get_setting(db, "SLOT_INTERVAL", int),
        DEBT_COOLDOWN=get_setting(db, "DEBT_COOLDOWN", int),
        MAX_TICKETS=get_setting(db, "MAX_TICKETS", int),
        MAX_SLOT_GAP=get_setting(db, "MAX_SLOT_GAP", int),
        MAX_SLOT_SEQUENCE=get_setting(db, "MAX_SLOT_SEQUENCE", int),
        MAX_USER_DEBT_STREAK=get_setting(db, "MAX_USER_DEBT_STREAK", int),
        MAX_LOGS=get_setting(db, "MAX_LOGS", int),
    )
#endregion

# ----------------------------

def get_user(id: int = None, tg_id: int = None, db: Session = Depends(get_db)):
    if not id and not tg_id:
        raise HTTPException(status_code=400, detail="Provide ?id= or ?tg=")
    if tg_id:
        user = db.execute(select(User).where(User.tg_id == tg_id)).scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="TG_USER_NOT_FOUND")

    else:
        user = db.get(User, id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
    return user



def check_ticket_rules(user: User, ticket_type: str, timestamp: datetime | None, db: Session):
    settings = load_settings(db)
    tt = db.execute(
        select(TicketType).where(TicketType.name == ticket_type)
    ).scalar_one_or_none()

    if not tt:
        raise HTTPException(status_code=400, detail="Wrong ticket type")

    # --- timestamp check logic ---
    from datetime import datetime, timedelta # TODO: (clean) wtf

    if timestamp:
        now = datetime.utcnow()

        # 1. только будущее
        if timestamp <= now:
            raise HTTPException(status_code=400, detail="TIMESTAMP_IN_PAST")

        # 2. проверка даты (должна быть в ближайшую или следующую пятницу)
        today = now.date()
        days_ahead = (settings.DEBT_WEEKDAY - today.weekday()) % 7
        if days_ahead == 0 and now.time() >= settings.START_TIME:
            days_ahead = 7
        first_friday = today + timedelta(days=days_ahead)
        second_friday = first_friday + timedelta(days=7)
        if timestamp.date() not in [first_friday, second_friday]:
            raise HTTPException(status_code=400, detail="Timestamp date must be on allowed days")

        # 3. проверка времени дня
        if not (settings.START_TIME <= timestamp.time() < settings.END_TIME):
            raise HTTPException(status_code=400, detail="Timestamp out of allowed time range")

        # 4. проверка кратности слоту
        if timestamp.minute % settings.SLOT_INTERVAL != 0 or timestamp.second != 0:
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
            raise HTTPException(status_code=400, detail="TIMESLOT_TAKEN")

        # 6. слот не входит в ближайшие 20 минут (--++--+--)
        # 16:10, 16:40, 16:50, 17:20, 17:30
        tickets = db.execute(
            select(Ticket.timestamp).where(
                Ticket.user_id == user.id,
                Ticket.status == "active",
            )
        ).scalars().all()

        # добавляем текущий слот
        all_times = sorted(tickets + [timestamp])

        # проверка: нельзя занимать более 2 слотов подряд или с одним промежутком
        for i in range(len(all_times)):
            count = 1
            for j in range(i+1, len(all_times)):
                diff_slots = (all_times[j] - all_times[j-1]).total_seconds() / 60 / settings.SLOT_INTERVAL
                if diff_slots <= settings.MAX_SLOT_GAP:  # два слота подряд или через один
                    count += 1
                    if count > settings.MAX_SLOT_SEQUENCE:
                        raise HTTPException(
                            status_code=400,
                            detail="MAX_SLOT_GAP_EXCEEDED"
                        )
                else:
                    break
        

    # --- cooldown logic --- # can be buggy, i hope not (none ticket type)
    if ticket_type == db.execute(select(TicketType.name)).scalars().first():
        # get last ticket and check if N minutes have passed
        last_ticket = db.execute(
            select(Ticket)
            .order_by(Ticket.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        # print(f"tt: {ticket_type},\n lt: {last_ticket}")
        if last_ticket and last_ticket.ticket_type and last_ticket.ticket_type.name == ticket_type:
            from datetime import datetime, timedelta
            now = datetime.utcnow()
            cooldown = settings.DEBT_COOLDOWN
            if last_ticket.created_at and (now - last_ticket.created_at) < timedelta(minutes=cooldown):
                raise HTTPException(
                    status_code=400,
                    detail=f"TICKET_COOLDOWN"
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
            detail="USER_MAX_TICKETS_EXCEEDED"
        )

    # --- debt-specific logic (kept but simplified) ---
    if tt.name == "debt":
        last_debt_user_id = db.execute(
            select(Ticket.user_id)
            .where(Ticket.ticket_type_id == tt.id)
            .order_by(Ticket.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        if last_debt_user_id == user.id and user.debt_streak >= settings.MAX_USER_DEBT_STREAK:
            raise HTTPException(
                status_code=400,
                detail=f"DEBT_MAX_STREAK_EXCEEDED"
            )

        # reset streaks for others
        others = db.execute(
            select(User).where(User.id != user.id, User.debt_streak >= settings.MAX_USER_DEBT_STREAK)
        ).scalars().all()

        for u in others:
            u.debt_streak = 0
            db.add(u)

def generate_ticket_number(db: Session, ticket_type: str = "", last_number: int = 0):
    settings = load_settings(db)
    prefix = "None"
    if ticket_type:
        prefix = db.execute(
            select(TicketType.symbol).where(TicketType.name == ticket_type)
        ).scalar_one_or_none()

    if not last_number:
        last_number = db.execute(
            select(Ticket.number)
            .order_by(Ticket.id.desc())
            .limit(1)
        ).scalar() or 0
    else: last_number -= 1

    # print(f"last: {last_number}")

    if last_number >= settings.MAX_TICKETS:
        number = 0
    else:
        number = last_number + 1

    name = f"{prefix}-{str(number).zfill(4)}"
    return name, number



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
    settings = load_settings(db)
    today = datetime.now().date()

    # вычисляем ближайшую и следующую пятницу (как в get_days)
    days_ahead = (settings.DEBT_WEEKDAY - today.weekday()) % 7
    if days_ahead == 0 and datetime.now().time() >= settings.START_TIME:
        days_ahead = 7

    dates = [
        today + timedelta(days=days_ahead),
        today + timedelta(days=days_ahead + 7),
    ]

    result = []

    for d in dates:
        start_time = datetime.combine(d, settings.START_TIME)
        end_time = datetime.combine(d, settings.END_TIME)

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

            current += timedelta(minutes=settings.SLOT_INTERVAL)

        result.append({
            "date": d.isoformat(),
            "slots": slots,
        })

    return result



#region --- LOGS ---
def safe_json(raw: bytes, limit: int = 2000):
    if not raw:
        return None
    try:
        text = raw.decode("utf-8")
        if len(text) > limit:
            text = text[:limit] + "...truncated"
        return json.loads(text)
    except Exception:
        return {"raw": raw[:limit].decode("utf-8", errors="ignore")}
    

# def extract_user(request):
#     # пример: id
#     id = request.query_params.get("id")
#     if id:
#         try:
#             return int(id)
#         except ValueError:
#             return None
#     else:
#         id = request.query_params.get("tg_id")
#     return None
#endregion --- --- ---