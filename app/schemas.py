# app/schemas.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# --- Ticket ---
class TicketOut(BaseModel):
    id: int
    name: str
    status: str
    timestamp: Optional[datetime]
    created_at: datetime
    user_id: int
    ticket_type_id: int

    class Config:
        from_attributes = True

# --- User ---
class UserOut(BaseModel):
    id: int
    tg_id: Optional[str]
    name: str
    course_id: Optional[int]
    debt_streak: int

    class Config:
        from_attributes = True

# --- TicketType ---
class TicketTypeOut(BaseModel):
    id: int
    name: str
    title: Optional[str]
    max_per_user: int
    require_time: Optional[int]
    symbol: Optional[str]

    class Config:
        from_attributes = True

# --- Course ---
class CourseOut(BaseModel):
    id: int
    name: str
    weekday: int
    start_time: str  # оставляем str для API
    end_time: str
    slot_range: int
    ticket_types: List[TicketTypeOut] = []  # вложенные типы билетов

    class Config:
        from_attributes = True

# --- Сборный вывод для /all/ ---
class AllDataOut(BaseModel):
    users: List[UserOut]
    courses: List[CourseOut]
    ticket_types: List[TicketTypeOut]
    tickets: List[TicketOut]

    class Config:
        from_attributes = True