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


@app.get("/tickets/")
def read_tickets():
    with Session(engine) as session:
        tickets = session.exec(select(Tickets)).all()
        return tickets
    
@app.post("/tickets/")
def create_ticket(ticket: Tickets):
    with Session(engine) as session:
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        return ticket
    

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


# list of avaliable tickets on date
# @app.get("/available_tickets/{date}")
# def available_tickets(date: str):
#     from datetime import datetime

#     try:
#         query_date = datetime.strptime(date, "%Y-%m-%d").date()
#     except ValueError:
#         raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

#     with Session(engine) as session:
#         booked_tickets = session.exec(
#             select(Tickets).where(Tickets.timestamp.cast(Date) == query_date)
#         ).all()
#         booked_numbers = {ticket.number for ticket in booked_tickets}

#         all_ticket_numbers = {f"{i:04d}" for i in range(10000)}
#         available_numbers = all_ticket_numbers - booked_numbers

#         return {"available_tickets": sorted(list(available_numbers))}