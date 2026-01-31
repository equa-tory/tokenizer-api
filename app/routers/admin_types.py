from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.models import *
from app.db import get_db
from app.schemas import AdminTicketTypeIn

router = APIRouter()


@router.post("/")
def upsert_ticket_type(
    id: Optional[int] = None,
    name: str = Query(...),
    title: Optional[str] = None,
    max_per_user: Optional[int] = None,
    require_time: Optional[int] = None,
    symbol: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # --- UPDATE ---
    if id is not None:
        tt = db.query(TicketType).filter(TicketType.id == id).first()
        if not tt:
            raise HTTPException(status_code=404, detail="TicketType not found")

        if title is not None:
            tt.title = name
        if max_per_user is not None:
            tt.max_per_user = max_per_user
        if require_time is not None:
            tt.require_time = require_time
        if symbol is not None: 
            tt.symbol = symbol

        db.commit()
        db.refresh(tt)
        return {"mode": "updated", "ticket_type": tt}

    tt = TicketType(
        name=name,
        title=title or name,
        max_per_user=max_per_user or 1,
        require_time=require_time or 0,
        symbol=symbol or name[0].upper()
    )

    db.add(tt)
    db.commit()
    db.refresh(tt)
    return {"mode": "created", "ticket_type": tt}