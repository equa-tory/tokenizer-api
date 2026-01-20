import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models import Course
from app.db import get_db

router = APIRouter()

@router.get("/")
def get_days(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).get(course_id)
    if not course:
        raise HTTPException(404)

    today = datetime.datetime.now().date()
    days_ahead = (course.weekday - today.weekday()) % 7
    if days_ahead == 0 and datetime.datetime.now().time() >= course.start_time:
        days_ahead = 7
    first_friday = today + datetime.timedelta(days=days_ahead)
    second_friday = first_friday + datetime.timedelta(days=7)
    return {"fridays": [first_friday.isoformat(), second_friday.isoformat()]}
