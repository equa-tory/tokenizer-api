from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Log

router = APIRouter()

@router.get("/")
def get_last_logs(
    limit: int = Query(16, ge=1, le=500),
    db: Session = Depends(get_db)
):
    logs = (
        db.query(Log)
        .order_by(Log.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": l.id,
            "kind": l.kind,
            "action": l.action,
            # "user_id": l.user_id,
            "status_code": l.status_code,
            "data": l.data,
            "created_at": l.created_at,
        }
        for l in logs
    ]