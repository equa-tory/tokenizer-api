from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base
from time import sleep

DATABASE_URL = "postgresql://postgres:postgres@db:5432/fastapidb"

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