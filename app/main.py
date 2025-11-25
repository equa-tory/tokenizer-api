# TODO:
# - Add date check so people can't book tickets for wierd dates
# - add more checks or validations
# - check time and date for tickets so there won't be multiple tickets at same time (exploit)
# - check type of ticket if it's valid
# - redo status


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


@app.get("/tickets/")
def read_tickets():
    with Session(engine) as session:
        tickets = session.exec(select(Tickets)).all()
        return tickets
    

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
        existing = session.exec(
            select(Tickets).where(Tickets.user_id == user_id)
        ).all()

        # count by type
        count_dept = sum(1 for t in existing if t.type == "dept")

        # streak check: if user already has dept_streak >= 2 and was the last to take dept, block
        if type == "dept" and user_id == session.exec(
            select(Tickets.user_id).where(Tickets.type == "dept").order_by(Tickets.timestamp.desc())
        ).first() and session.get(Users, user_id).dept_streak >= 2:
            raise HTTPException(status_code=400, detail="Cannot take dept ticket consecutively more than twice")

        if type == "dept":
            frozen_users = session.exec(select(Users).where(Users.dept_streak >= 2)).all()
            for u in frozen_users:
                u.dept_streak = 0
                session.add(u)
            session.commit()

        # only 5 dept allowed total
        if type == "dept" and count_dept >= 5:
            raise HTTPException(status_code=400, detail="Max dept tickets reached")

        # only 1 ticket for non-dept types
        if type != "dept" and any(t.type == type for t in existing):
            raise HTTPException(status_code=400, detail="Already has one ticket of this type")
        
        last_ticket = session.exec(
            select(Tickets).order_by(Tickets.number.desc())
        ).first()
        if last_ticket:
            ticket_number = int(last_ticket.number) + 1
        else:
            ticket_number = 1
        ticket_number = str(ticket_number).zfill(4)

        ticket = Tickets(number=ticket_number, type=type, user_id=user_id, timestamp=timestamp)
        session.add(ticket)
        session.commit()
        session.refresh(ticket)

        if type == "dept":
            u = session.get(Users, user_id)
            u.dept_streak += 1
            session.add(u)
            session.commit()

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
@app.get("/user/{user_id}/tickets")
def user_tickets(user_id: int):
    with Session(engine) as session:
        tickets = session.exec(
            select(Tickets).where(Tickets.user_id == user_id)
        ).all()
        return tickets
    

@app.get("/user/{user_id}/")
def user_status(user_id: int):
    with Session(engine) as session:
        user = session.get(Users, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "name": user.name,
            "dept_streak": user.dept_streak,
            "telegram_id": user.telegram_id
        }