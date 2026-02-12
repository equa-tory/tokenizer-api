from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.logic import load_settings

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

    settings = load_settings(db)
    if settings.MAX_LOGS >= 0:
        total_logs = db.query(func.count(Log.id)).scalar()
        if total_logs > settings.MAX_LOGS:
            # Calculate how many logs to delete
            to_delete_count = total_logs - settings.MAX_LOGS
            # Fetch the oldest logs to delete
            old_logs = (
                db.query(Log)
                .order_by(Log.created_at.asc())
                .limit(to_delete_count)
                .all()
            )
            for old_log in old_logs:
                db.delete(old_log)
            db.commit()

    return [
        {
            "id": l.id,
            "kind": l.kind,
            "action": l.action,
            "status_code": l.status_code,
            "data": l.data,
            "created_at": l.created_at,
        }
        for l in logs
    ]