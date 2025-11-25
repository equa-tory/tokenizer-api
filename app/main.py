# TODO:
# - Add validation so random request countn't be used (only via *our systems*)
# - create users in other way (not via API)


import time
from fastapi import FastAPI, HTTPException, Query
from datetime import datetime, timedelta, time as dt_time
from models import *
from sqlalchemy import func



valid_types = {
    "debt": "Сдача задолженностей", # !!! keep this line like that, required by telegram bot logic !!!
    "exam": "Сдача экзамена",
    "zachet": "Сдача зачёта",
    "report": "Сдача отчёта",
    "diploma": "Сдача диплома",
}

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

def validate_tg_user(user_id: int):
    with Session(engine) as session:
        user = session.exec(select(Users).where(Users.telegram_id == user_id)).first()
        if not user:
            # создаём нового пользователя с TG ID
            user = Users(name=f"TG_{user_id}", telegram_id=user_id)
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

# TODO: validation middleware
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

@app.get("/get_valid_types/")
def get_valid_types():
    return {"valid_types": valid_types}

# return next two fridays from today
@app.get("/get_fridays/")
def get_fridays():
    today = datetime.datetime.now().date()
    fridays = []
    days_ahead = (4 - today.weekday()) % 7
    if days_ahead == 0 and datetime.datetime.now().time() >= datetime.datetime.strptime("16:00", "%H:%M").time():
        days_ahead = 7
    first_friday = today + timedelta(days=days_ahead)
    second_friday = first_friday + timedelta(days=7)
    
    fridays.append({
        "date": first_friday.isoformat(),
        "label": first_friday.strftime("%d %B")
    })
    fridays.append({
        "date": second_friday.isoformat(),
        "label": second_friday.strftime("%d %B")
    })
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
@app.get("/ticket/check/{date}&{type}")
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

# book ticket, example: /ticket/book/?tg=1&debt&2024-07-12T12:42:20
@app.post("/ticket/book")
def book_ticket(
    type: str = Query(...),
    timestamp: datetime.datetime = Query(None),
    id: int = Query(None),
    tg: int = Query(None)
):
    # --- User ID selection ---
    if id is None and tg is None:
        raise HTTPException(status_code=400, detail="Provide ?id= or ?tg=")

    with Session(engine) as session:
        # TG user
        if tg is not None:
            user = session.exec(select(Users).where(Users.telegram_id == tg)).first()
            if not user:
                user = Users(name=f"TG_{tg}", telegram_id=tg)
                session.add(user)
                session.commit()
                session.refresh(user)
            user_id = user.id

        # Normal user
        else:
            user = session.get(Users, id)
            if not user:
                raise HTTPException(status_code=404, detail="Пользователь не найден")
            user_id = user.id

        # --- Validation ---
        if type not in valid_types.keys():
            raise HTTPException(status_code=400, detail="Неверный тип билета")

        # If debt — timestamp required
        if type == "debt":
            if timestamp is None:
                raise HTTPException(status_code=400, detail="Требуется время для задолженности")
            validate_ticket_timestamp(timestamp)

            existing_slot = session.exec(
                select(Tickets).where(Tickets.timestamp == timestamp)
            ).first()
            if existing_slot:
                raise HTTPException(status_code=400, detail="Слот уже забронирован")

        # --- Get existing tickets of user ---
        existing = session.exec(
            select(Tickets).where(Tickets.user_id == user_id)
        ).all()

        # Max 5 debt
        if type == "debt":
            count_debt = sum(1 for t in existing if t.type == "debt")
            if count_debt >= 5:
                raise HTTPException(status_code=400, detail="Максимум задолженностей достигнут")

            # consecutive check
            last_debt_user_id = session.exec(
                select(Tickets.user_id)
                .where(Tickets.type == "debt")
                .order_by(Tickets.timestamp.desc())
            ).first()

            if last_debt_user_id == user_id and user.debt_streak >= 2:
                raise HTTPException(status_code=400, detail="Нельзя брать задолженность более двух раз подряд")

            # unfreeze all if someone else takes debt
            frozen_users = session.exec(select(Users).where(Users.debt_streak >= 2)).all()
            for u in frozen_users:
                u.debt_streak = 0
                session.add(u)

        # Non-debt: only 1 ticket
        if type != "debt" and any(t.type == type for t in existing):
            raise HTTPException(status_code=400, detail="Уже есть билет этого типа")

        # --- Ticket numbering ---
        last_ticket = session.exec(
            select(Tickets).order_by(Tickets.number.desc())
        ).first()
       
        # --- Ticket numbering with prefix ---
        prefix_map = {
            "exam": "Э",
            "zachet": "Ё",
            "debt": "З",
            "diploma": "Д",
            "report": "О"
        }
        last_number_int = int(last_ticket.number[1:]) if last_ticket else 0
        ticket_number = f"{prefix_map[type]}-{str(last_number_int + 1).zfill(4)}"
       
        # --- Create ticket ---
        ticket = Tickets(
            number=ticket_number,
            type=type,
            user_id=user_id,
            timestamp=timestamp if timestamp else None
        )

        session.add(ticket)

        if type == "debt":
            user.debt_streak += 1
            session.add(user)

        session.commit()
        session.refresh(ticket)

        return ticket

# cancel
@app.post("/ticket/cancel/{ticket_id}")
def cancel_ticket(ticket_id: int):
    with Session(engine) as session:
        ticket = session.get(Tickets, ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        session.delete(ticket)
        session.commit()
        return {"detail": "Ticket canceled"}

# status
@app.get("/status")
def status(id: int = Query(None), tg: int = Query(None)):
    if id is None and tg is None:
        raise HTTPException(status_code=400, detail="Provide ?id= or ?tg=")

    with Session(engine) as session:
        # ---- TG user ----
        if tg is not None:
            user = session.exec(select(Users).where(Users.telegram_id == tg)).first()
            if not user:
                user = Users(name=f"TG_{tg}", telegram_id=tg)
                session.add(user)
                session.commit()
                session.refresh(user)

        # ---- Normal user ----
        else:
            user = session.get(Users, id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

        # ---- Get tickets ----
        tickets = session.exec(
            select(Tickets).where(Tickets.user_id == user.id)
        ).all()

        # ---- Last queued ticket ----
        last_ticket = session.exec(
            select(Tickets)
            .where(Tickets.user_id == user.id)
            .order_by(Tickets.timestamp.desc())
        ).first()

        return {
            "id": user.id,
            "name": user.name,
            "debt_streak": user.debt_streak,
            "telegram_id": user.telegram_id,
            "tickets": tickets,
            "last_ticket": last_ticket
        }