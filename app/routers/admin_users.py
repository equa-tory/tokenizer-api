from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.models import User
from app.db import get_db


router = APIRouter()


@router.post("/")
def upsert_user(
    id: Optional[int] = None,
    name: Optional[str] = None,
    course_id: Optional[int] = None,
    tg_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if id:
        user = db.query(User).get(id)
        if not user:
            raise HTTPException(404)

        if name: user.name = name
        if course_id: user.course_id = course_id
        if tg_id: user.tg_id = tg_id

        db.commit()
        return {"mode": "updated", "user": user}

    if not name or not course_id:
        raise HTTPException(400)

    user = User(name=name, course_id=course_id, tg_id=tg_id)
    db.add(user)
    db.commit()
    return {"mode": "created", "user": user}