from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models import Base, TicketType, Setting
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


# --- Default settings -----------------------
# loog in config.py
DEFAULT_SETTINGS = {
    "DEBT_WEEKDAY": 4, # friday (def: 4)
    "START_TIME": "16:00", # (def: 16:00)
    "END_TIME": "18:00", # (def: 18:00)
    "SLOT_INTERVAL": 10, # (def: 10)
    "DEBT_COOLDOWN": 0, # (def: 15)
    "MAX_TICKETS": 9999, # (def: 9999)
    "MAX_SLOT_GAP": 1, # (def: 1)
    "MAX_SLOT_SEQUENCE": 2, # (def: 2)
    "MAX_USER_DEBT_STREAK": 5, # (def: 2)
    "MAX_LOGS": -1, # -1 = no limit
}

def ensure_default_settings(db: Session):
    existing = {s.key for s in db.query(Setting.key).all()}

    to_create = [
        Setting(key=k, value=str(v))
        for k, v in DEFAULT_SETTINGS.items()
        if k not in existing
    ]

    if to_create:
        db.add_all(to_create)
        db.commit()

# --- Ensure default necessary TicketTypes exist -----------------------
def ensure_default_tickettypes(db: Session) -> None:
    defaults = [
        {
            "name": "debt",
            "title": "Сдача Задолженностей",
            "max_per_day": 5,
            "require_time": 1,
            "symbol": "З",
        },
        {
            "name": "zachet",
            "title": "Сдача Зачёта",
            "max_per_day": 1,
            "require_time": 0,
            "symbol": "Ë",
        },
        {
            "name": "exam",
            "title": "Сдача Экзамена",
            "max_per_day": 1,
            "require_time": 0,
            "symbol": "Э",
        },
        {
            "name": "report",
            "title": "Сдача Отчёта",
            "max_per_day": 1,
            "require_time": 0,
            "symbol": "О",
        },
        {
            "name": "diploma",
            "title": "Сдача Диплома",
            "max_per_day": 1,
            "require_time": 0,
            "symbol": "Д",
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