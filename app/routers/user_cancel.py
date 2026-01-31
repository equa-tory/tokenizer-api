# normal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import Course, Ticket, TicketType, User
from app.db import get_db
from datetime import datetime
from sqlalchemy import select
from app.schemas import UserCancelIn

router = APIRouter()


@router.post("/", response_model=UserCancelIn)
def cancel_ticket(
    ticket_id: str = Query(...),
    db: Session = Depends(get_db)
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(ticket)
    db.commit()
    return {"detail": "Ticket canceled"}