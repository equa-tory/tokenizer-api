from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
import datetime


class Users(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    dept_streak: int = Field(default=0)
    telegram_id: Optional[int] = None


class Tickets(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    number: str = Field(default="?-XXXX", max_length=6)
    type: Optional[str] = None
    status: str = Field(default="queued")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    timestamp: Optional[datetime.datetime] = Field(default_factory=None)


class Logs(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    action: str
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    ticket_id: Optional[int] = Field(default=None, foreign_key="tickets.id")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime)