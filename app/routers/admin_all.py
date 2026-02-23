from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import *
from app.db import get_db
from app.schemas import AdminAllIn

router = APIRouter()

@router.get("/")
def get_all(db: Session = Depends(get_db)):
    users = db.query(User).all()
    # courses = db.query(Course).all()
    ticket_types = db.query(TicketType).all()
    tickets = db.query(Ticket).all()

    # Создаём словарь course_id → список типов билетов
    # course_tt_map = {}
    # for course in courses:
    #     course_tt_map[course.id] = [{"id": tt.id, "name": tt.name, "max_per_day": tt.max_per_day, "require_time": tt.require_time} 
    #                                 for tt in course.ticket_types]

    # Формируем JSON с типами внутри курса
    # courses_out = []
    # for course in courses:
    #     courses_out.append({
    #         "id": course.id,
    #         "name": course.name,
    #         "weekday": course.weekday,
    #         "start_time": course.start_time.strftime("%H:%M:%S"),
    #         "end_time": course.end_time.strftime("%H:%M:%S"),
    #         "slot_range": course.slot_range,
    #         "ticket_types": course_tt_map.get(course.id, [])
    #     })

    settings_out = []
    for setting in db.query(Setting).all():
        settings_out.append({
            "key": setting.key,
            "value": setting.value,
        })

    return {
        "settings": settings_out,
        "users": [{"id": u.id, "name": u.name, "tg_id": u.tg_id, "course_id": u.course_id, "debt_streak": u.debt_streak} for u in users],
        #"courses": courses_out,
        "ticket_types": [{"id": tt.id, "name": tt.name, "title": tt.title, "max_per_day": tt.max_per_day, "require_time": tt.require_time, "symbol": tt.symbol} for tt in ticket_types],
        "tickets": [{"id": t.id, "name": t.name, "number": t.number, "status": t.status, "user_id": t.user_id, "ticket_type_id": t.ticket_type_id, "timestamp": t.timestamp.isoformat() if t.timestamp else None, "created_at": t.created_at} for t in tickets],
    }