import csv
from fastapi import APIRouter, Depends, UploadFile, HTTPException, Response
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from io import StringIO

router = APIRouter()


@router.post("/")
async def backup_users(file: UploadFile = None, db: Session = Depends(get_db)):
    if file:
        if not file.filename.endswith(".csv"):
            raise HTTPException(400, detail="Only CSV files are allowed")

        content = await file.read()
        lines = content.decode("utf-8").splitlines()
        reader = csv.DictReader(lines)

        users_to_add = []

        for row in reader:
            tg_id = row.get("tg_id")
            name = row.get("name")

            if not name:
                continue  # пропускаем пустые строки

            # проверяем дубликаты по tg_id
            existing = None
            if tg_id:
                existing = db.query(User).filter_by(tg_id=int(tg_id)).first()

            if existing:
                # обновляем имя если tg_id уже есть
                existing.name = name
            else:
                users_to_add.append(User(
                    name=name,
                    tg_id=int(tg_id) if tg_id else None
                ))

        if users_to_add:
            db.add_all(users_to_add)

        db.commit()
        return {"imported": len(users_to_add)}

    else:
        users = db.query(User).all()
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["tg_id", "name"])
        for user in users:
            writer.writerow([user.tg_id if user.tg_id is not None else "", user.name])
        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=users_backup.csv"
        return response