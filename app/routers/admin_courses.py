from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import *
from app.db import get_db

router = APIRouter()

@router.post("/")
def upsert_course(
    id: Optional[int] = None,
    name: Optional[str] = None,
    weekday: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    slot_range: Optional[int] = None,
    ticket_type_ids: list[int] = Query(default=[]),
    db: Session = Depends(get_db),
):
    # --- UPDATE ---
    if id is not None:
        course = db.query(Course).filter(Course.id == id).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        if name is not None:
            course.name = name
        if weekday is not None:
            course.weekday = weekday
        if start_time is not None:
            course.start_time = start_time
        if end_time is not None:
            course.end_time = end_time
        if slot_range is not None:
            course.slot_range = slot_range

        if ticket_type_ids:
            course.ticket_types = db.query(TicketType).filter(
                TicketType.id.in_(ticket_type_ids)
            ).all()

        db.commit()
        db.refresh(course)
        return {"mode": "updated", "course": course}

    # --- CREATE ---
    if name is None:
        raise HTTPException(status_code=400, detail="name is required for create")

    course = Course(
        name=name,
        weekday=weekday or 4,
        start_time=start_time or "16:00:00",
        end_time=end_time or "18:00:00",
        slot_range=slot_range or 10,
    )

    if ticket_type_ids:
        course.ticket_types = db.query(TicketType).filter(
            TicketType.id.in_(ticket_type_ids)
        ).all()

    db.add(course)
    db.commit()
    db.refresh(course)

    return {"mode": "created", "course": course}