# TODO:
# - Add date check so people can't book tickets for wierd dates
# - add more checks or validations


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

# @app.get("/")
# def read_root():
#     return {"Hello": "World"}


# TODO: remomve
@app.post("/users/")
def create_user(user: Users):
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

# @app.get("/users/")
# def read_users():
#     with Session(engine) as session:
#         users = session.exec(select(Users)).all()
#         return users


@app.get("/tickets/")
def read_tickets():
    with Session(engine) as session:
        tickets = session.exec(select(Tickets)).all()
        return tickets
    
# @app.post("/tickets/")
# def create_ticket(ticket: Tickets):
#     with Session(engine) as session:
#         session.add(ticket)
#         session.commit()
#         session.refresh(ticket)
#         return ticket
    

# return next two fridays from today
@app.get("/get_fridays/")
def get_fridays():
    from datetime import datetime, timedelta

    today = datetime.now()
    fridays = []
    days_ahead = 4 - today.weekday()  # Friday is 4
    if days_ahead <= 0:
        days_ahead += 7
    first_friday = today + timedelta(days=days_ahead)
    fridays.append(first_friday.date())

    second_friday = first_friday + timedelta(days=7)
    fridays.append(second_friday.date())

    return {"fridays": fridays}


# list of avaliable tickets on date with type (date&type) format: YYYY-MM-DD&<type>
@app.get("/available_tickets/{date}&{type}")
def available_tickets(date: str, type: str):
    from datetime import datetime, date as dt_date
    from sqlalchemy import func

    query_date = datetime.strptime(date, "%Y-%m-%d").date()
    with Session(engine) as session:
        tickets = session.exec(
            select(Tickets).where(
                func.date(Tickets.timestamp) == query_date,
                Tickets.type == type
            )
        ).all()
        return tickets
    

# book ticket, example: /book_ticket/1&dept&2024-07-12T12:42:20
@app.post("/book_ticket/{user_id}&{type}&{timestamp}")
def book_ticket(user_id: int, type: str, timestamp: datetime.datetime):
    with Session(engine) as session:
        ticket = Tickets(type=type, user_id=user_id, timestamp=timestamp)
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return ticket
    

# cancel
@app.post("/cancel_ticket/{ticket_id}")
def cancel_ticket(ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Tickets, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        session.delete(ticket)
        session.commit()
        return {"detail": "Ticket canceled"}


# check own tickets
@app.get("/use_tickets/{user_id}")
def use_tickets(user_id: int):
    with Session(engine) as session:
        tickets = session.exec(
            select(Tickets).where(Tickets.user_id == user_id)
        ).all()
        return tickets