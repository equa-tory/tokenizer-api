from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.models import *
from app.db import get_db


router = APIRouter()


@router.post("/")
def upsert_ticket_type(
    id: Optional[int] = None,
    name: Optional[str] = None,
    max_per_user: Optional[int] = None,
    require_time: Optional[int] = None,
    db: Session = Depends(get_db)
):
    # --- UPDATE ---
    if id is not None:
        tt = db.query(TicketType).filter(TicketType.id == id).first()
        if not tt:
            raise HTTPException(status_code=404, detail="TicketType not found")

        if name is not None:
            tt.name = name
        if max_per_user is not None:
            tt.max_per_user = max_per_user
        if require_time is not None:
            tt.require_time = require_time

        db.commit()
        db.refresh(tt)
        return {"mode": "updated", "ticket_type": tt}

    # --- CREATE ---
    if name is None or max_per_user is None:
        raise HTTPException(status_code=400, detail="name and max_per_user are required")

    tt = TicketType(
        name=name,
        max_per_user=max_per_user,
        require_time=require_time
    )

    db.add(tt)
    db.commit()
    db.refresh(tt)
    return {"mode": "created", "ticket_type": tt}