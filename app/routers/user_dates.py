import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Course
from app.db import get_db
from logic import START_TIME, END_TIME, SLOT_INTERVAL, DEBT_WEEKDAY
from app.schemas import UserTimeslotsIn

router = APIRouter()

# course dates
# @router.get("/")
# def get_days(course_id: int, db: Session = Depends(get_db)):
#     course = db.query(Course).get(course_id)
#     if not course:
#         raise HTTPException(404)

#     today = datetime.datetime.now().date()
#     days_ahead = (course.weekday - today.weekday()) % 7
#     if days_ahead == 0 and datetime.datetime.now().time() >= course.start_time:
#         days_ahead = 7
#     first_friday = today + datetime.timedelta(days=days_ahead)
#     second_friday = first_friday + datetime.timedelta(days=7)
#     return [first_friday.isoformat(), second_friday.isoformat()


# all fridays
@router.get("/")
def get_days(db: Session = Depends(get_db)):
    today = datetime.datetime.now().date()
    days_ahead = (DEBT_WEEKDAY - today.weekday()) % 7
    if days_ahead == 0 and datetime.datetime.now().time() >= START_TIME:
        days_ahead = 7
    first_friday = today + datetime.timedelta(days=days_ahead)
    second_friday = first_friday + datetime.timedelta(days=7)
    return [first_friday.isoformat(), second_friday.isoformat()]
