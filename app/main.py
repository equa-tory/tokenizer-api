# TODO:
# - Add validation so random request countn't be used (only via *our systems*)
# - create users in other way (not via API)
# - use telegram id !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# - change ticket number to "N-XXXX" format
# - redo status last ticket


import time
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta, time as dt_time
from models import *
from sqlalchemy import func



valid_types = ["dept", "exam", "test", "diploma", "report"]

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


# --- Validation middlewares -----------------------

# TODO: 
# @app.middleware("http")
# async def verify_source(request: Request, call_next):
#     if request.url.path.startswith("/book_ticket"):
#         # простой пример: проверяем кастомный header
#         if request.headers.get("X-Auth-Token") != "SECRET_SYSTEM_TOKEN":
#             return JSONResponse(status_code=403, content={"detail": "Forbidden"})
#     response = await call_next(request)
#     return response


def validate_ticket_timestamp(timestamp: datetime.datetime):
    today = datetime.datetime.now()

    # ближайшие две пятницы
    days_ahead = 4 - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    first_friday = (today + timedelta(days=days_ahead)).date()
    second_friday = (first_friday + timedelta(days=7))  # уже дата

    if timestamp.date() not in [first_friday, second_friday]:
        raise HTTPException(status_code=400, detail="Tickets can only be booked for this or next Friday")

    # Время 16:00-18:00
    start_time = dt_time(16, 0)
    end_time = dt_time(18, 0)
    if not (start_time <= timestamp.time() <= end_time):
        raise HTTPException(status_code=400, detail="Ticket time must be between 16:00-18:00")

    # Слоты по 10 минут
    if timestamp.minute % 10 != 0 or timestamp.second != 0:
        raise HTTPException(status_code=400, detail="Ticket must be booked on a 10-minute slot")

# --- Requests ---------------------------------------

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

    today = datetime.datetime.now()
    fridays = []
    days_ahead = 4 - today.weekday()  # Friday is 4
    if days_ahead <= 0:
        days_ahead += 7
    first_friday = today + timedelta(days=days_ahead)
    fridays.append(first_friday.date())

    second_friday = first_friday + timedelta(days=7)
    fridays.append(second_friday.date())

    return {"fridays": fridays}


# return timeslots for a given friday + check if not taken
@app.get("/get_timeslots/{friday_date}")
def get_timeslots(friday_date: str):
    with Session(engine) as session:
        try:
            query_date = datetime.datetime.strptime(friday_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

        today = datetime.datetime.now().date()
        days_ahead = 4 - today.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        first_friday = today + timedelta(days=days_ahead)
        second_friday = first_friday + timedelta(days=7)

        if query_date not in [first_friday, second_friday]:
            raise HTTPException(status_code=400, detail="Date must be this or next Friday.")

        timeslots = []
        start_time = datetime.datetime.combine(query_date, dt_time(16, 0))
        end_time = datetime.datetime.combine(query_date, dt_time(18, 0))

        current_slot = start_time
        while current_slot < end_time:
            # проверка, занят ли слот
            existing_ticket = session.exec(
                select(Tickets).where(Tickets.timestamp == current_slot)
            ).first()
            timeslots.append({
                "time": current_slot.time().strftime("%H:%M"),
                "available": existing_ticket is None
            })
            current_slot += timedelta(minutes=10)

        return {"timeslots": timeslots}


# list of avaliable tickets on date with type (date&type) format: YYYY-MM-DD&<type>
@app.get("/available_tickets/{date}&{type}")
def available_tickets(date: str, type: str):
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
@app.post("/book_ticket/{user_id}&{type}&{timestamp}")  # TODO: add timestamp (10 minutes + fridays) validation
# def book_ticket(user_id: int, type: str, timestamp: datetime):
def book_ticket(user_id: int, type: str, timestamp: datetime.datetime):
    validate_ticket_timestamp(timestamp)
    with Session(engine) as session:
        # duplicate timestamp check
        existing = session.exec(
            select(Tickets).where(Tickets.timestamp == timestamp)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Ticket already booked for this time")
        
        # user existence check
        user = session.get(Users, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # get existing tickets
        existing = session.exec(
            select(Tickets).where(Tickets.user_id == user_id)
        ).all()

        # type check
        if type not in valid_types:
            raise HTTPException(status_code=400, detail="Invalid ticket type")

        # count by type
        count_dept = sum(1 for t in existing if t.type == "dept")

        # streak check
        last_dept_user_id = session.exec(
            select(Tickets.user_id).where(Tickets.type == "dept").order_by(Tickets.timestamp.desc())
        ).first()
        if type == "dept" and last_dept_user_id == user_id and user.dept_streak >= 2:
            raise HTTPException(status_code=400, detail="Cannot take dept ticket consecutively more than twice")

        # reset dept_streak for frozen users
        if type == "dept":
            frozen_users = session.exec(select(Users).where(Users.dept_streak >= 2)).all()
            for u in frozen_users:
                u.dept_streak = 0
                session.add(u)

        # max 5 dept tickets
        if type == "dept" and count_dept >= 5:
            raise HTTPException(status_code=400, detail="Max dept tickets reached")

        # only 1 ticket for non-dept types
        if type != "dept" and any(t.type == type for t in existing):
            raise HTTPException(status_code=400, detail="Already has one ticket of this type")
        
        last_ticket = session.exec(
            select(Tickets).order_by(Tickets.number.desc())
        ).first()
        ticket_number = str(int(last_ticket.number)+1 if last_ticket else 1).zfill(4)

        ticket = Tickets(number=ticket_number, type=type, user_id=user_id, timestamp=timestamp)
        session.add(ticket)

        # increment dept_streak if needed
        if type == "dept":
            user.dept_streak += 1
            session.add(user)

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
@app.get("/user/{user_id}/tickets")
def user_tickets(user_id: int):
    with Session(engine) as session:
        tickets = session.exec(
            select(Tickets).where(Tickets.user_id == user_id)
        ).all()
        return tickets

@app.get("/tg/user/{tg_id}/tickets")
def tg_user_tickets(tg_id: int):
    with Session(engine) as session:
        user = session.exec(select(Users).where(Users.telegram_id == tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        tickets = session.exec(
            select(Tickets).where(Tickets.user_id == user.id)
        ).all()
        return tickets


# status
@app.get("/user/{user_id}/status")
def user_status(user_id: int):
    with Session(engine) as session:
        user = session.get(Users, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # get last ticket
        # last_ticket = session.exec(
        #     select(Tickets).order_by(Tickets.id.desc())
        # ).first()

        # last_ticket_data = None
        # if last_ticket:
        #     last_ticket_data = {
        #         "id": last_ticket.id,
        #         "number": last_ticket.number,
        #         "type": last_ticket.type,
        #         "user_id": last_ticket.user_id,
        #         "timestamp": last_ticket.timestamp
        #     }

        return {
            "id": user.id,
            "name": user.name,
            "dept_streak": user.dept_streak,
            "telegram_id": user.telegram_id,
            # "last_ticket": last_ticket_data
        }

@app.get("/tg/user/{user_id}/status")
def tg_user_status(tg_id: int):
    with Session(engine) as session:
        user = session.exec(select(Users).where(Users.telegram_id == tg_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # get last ticket
        # last_ticket = session.exec(
        #     select(Tickets).order_by(Tickets.id.desc())
        # ).first()

        # last_ticket_data = None
        # if last_ticket:
        #     last_ticket_data = {
        #         "id": last_ticket.id,
        #         "number": last_ticket.number,
        #         "type": last_ticket.type,
        #         "user_id": last_ticket.user_id,
        #         "timestamp": last_ticket.timestamp
        #     }

        return {
            "id": user.id,
            "name": user.name,
            "dept_streak": user.dept_streak,
            "telegram_id": user.telegram_id,
            # "last_ticket": last_ticket_data
        }