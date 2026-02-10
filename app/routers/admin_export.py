import csv
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import StringIO

from app.db import get_db
from app.models import User

router = APIRouter()


@router.get("/")
def export_users_csv(db: Session = Depends(get_db)):
    users = db.query(User).all()

    buffer = StringIO()
    writer = csv.writer(buffer)

    # header
    writer.writerow([
        # "id",
        "name",
        "tg_id",
        # "course_id",
        # "debt_streak",
    ])

    for u in users:
        writer.writerow([
            # u.id,
            u.name,
            u.tg_id,
            # u.course_id,
            # u.debt_streak,
        ])

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        },
    )