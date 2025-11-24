import time
from fastapi import FastAPI, HTTPException
from models import *


DATABASE_URL = "postgresql://postgres:postgres@db:5432/fastapidb"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

app = FastAPI()


# A simple retry mechanism for database connection on startup
@app.on_event("startup")
def on_startup():
    for _ in range(5):
        try:
            create_db_and_tables()
            print("Database connected and tables created")
            return
        except Exception as e:
            print(f"Database connection failed, retrying in 5 seconds... Error: {e}")
            time.sleep(5)
    raise HTTPException(status_code=500, detail="Could not connect to the database")


# --- Requests ---------------------------------------

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/users/")
def create_user(user: Users):
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@app.get("/users/")
def read_users():
    with Session(engine) as session:
        users = session.exec(select(Users)).all()
        return users
