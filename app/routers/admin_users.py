from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.models import User
from app.db import get_db
from app.schemas import UserOut

router = APIRouter()


@router.post("/")
def upsert_user(
    id: Optional[int] = None,
    name: str = Query(...),
    course_id: Optional[int] = None,
    tg_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    if id:
        user = db.query(User).get(id)
        if not user:
            raise HTTPException(404)

        if name is not None:
            user.name = name
        if course_id is not None:
            user.course_id = course_id
        if tg_id is not None:
            user.tg_id = tg_id

        db.commit()
        db.refresh(user)
        return {"mode": "updated", "user": user}

    if not name:
        raise HTTPException(400, detail="Name is required for creating a new user")

    user = User(name=name, course_id=course_id, tg_id=tg_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"mode": "created", "user": user}