from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, TicketType
from time import sleep
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")



for _ in range(10):
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        break
    except Exception:
        sleep(2)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Ensure default necessary TicketTypes exist -----------------------
def ensure_default_tickettypes(db: Session) -> None:
    defaults = [
        {
            "name": "debt",
            "title": "Задолженность",
            "max_per_user": 5,
            "require_time": 1,
            "symbol": "З",
        },
        {
            "name": "zachet",
            "title": "Зачёт",
            "max_per_user": 1,
            "require_time": 0,
            "symbol": "Ë",
        },
    ]

    existing = {
        t.name for t in db.query(TicketType.name).all()
    }

    to_create = [
        TicketType(**item)
        for item in defaults
        if item["name"] not in existing
    ]

    if to_create:
        db.add_all(to_create)
        db.commit()