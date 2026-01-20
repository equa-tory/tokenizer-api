from datetime import datetime, timedelta, time as dt_time
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlalchemy import func

from models import (
    User,
    Ticket,
    TicketType,
    Course,
    Schedule,
    UserCourse,
)
from db import engine


# --- Users -------------------------------------------------

def get_or_create_user_by_tg(tg_id: int) -> User:
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.telegram_id == tg_id)
        ).first()
        if not user:
            user = User(name=f"TG_{tg_id}", telegram_id=tg_id)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user


def get_user_by_id(user_id: int) -> User:
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


# --- Schedule & time validation ----------------------------

def validate_timestamp_for_course(
    course_id: int,
    timestamp: datetime
):
    weekday = timestamp.weekday()

    with Session(engine) as session:
        schedules = session.exec(
            select(Schedule).where(Schedule.course_id == course_id)
        ).all()

        for s in schedules:
            if s.weekday != weekday:
                continue

            start_dt = datetime.combine(timestamp.date(), s.start_time)
            end_dt = datetime.combine(timestamp.date(), s.end_time)

            if not (start_dt <= timestamp <= end_dt):
                continue

            if ((timestamp.minute * 60 + timestamp.second) %
                (s.slot_minutes * 60)) != 0:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid time slot"
                )

            return  # valid

    raise HTTPException(
        status_code=400,
        detail="Timestamp not allowed by schedule"
    )


# --- Tickets -----------------------------------------------

def get_user_tickets(user_id: int, course_id: int):
    with Session(engine) as session:
        return session.exec(
            select(Ticket).where(
                Ticket.user_id == user_id,
                Ticket.course_id == course_id
            )
        ).all()


def generate_ticket_number(course_id: int, type_id: int) -> str:
    with Session(engine) as session:
        last_ticket = session.exec(
            select(Ticket)
            .where(
                Ticket.course_id == course_id,
                Ticket.type_id == type_id
            )
            .order_by(Ticket.id.desc())
        ).first()

        next_number = (last_ticket.id + 1) if last_ticket else 1
        return f"{course_id}-{type_id}-{str(next_number).zfill(4)}"


def book_ticket(
    *,
    course_id: int,
    type_key: str,
    user_id: int,
    timestamp: datetime | None,
):
    with Session(engine) as session:
        ticket_type = session.exec(
            select(TicketType).where(
                TicketType.course_id == course_id,
                TicketType.key == type_key
            )
        ).first()

        if not ticket_type:
            raise HTTPException(status_code=400, detail="Invalid ticket type")

        if ticket_type.requires_time:
            if not timestamp:
                raise HTTPException(
                    status_code=400,
                    detail="Timestamp required"
                )
            validate_timestamp_for_course(course_id, timestamp)

            existing_slot = session.exec(
                select(Ticket).where(Ticket.timestamp == timestamp)
            ).first()
            if existing_slot:
                raise HTTPException(
                    status_code=400,
                    detail="Time slot already taken"
                )

        existing = session.exec(
            select(Ticket).where(
                Ticket.user_id == user_id,
                Ticket.course_id == course_id,
                Ticket.type_id == ticket_type.id
            )
        ).all()

        if ticket_type.max_per_user is not None:
            if len(existing) >= ticket_type.max_per_user:
                raise HTTPException(
                    status_code=400,
                    detail="Ticket limit reached"
                )

        number = generate_ticket_number(course_id, ticket_type.id)

        ticket = Ticket(
            number=number,
            course_id=course_id,
            type_id=ticket_type.id,
            user_id=user_id,
            timestamp=timestamp,
        )

        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return ticket
