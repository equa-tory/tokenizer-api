from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
import datetime


class Users(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    is_frozen: bool = False


class Tickets(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    number: str = Field(default="0000", max_length=4)
    type: Optional[str] = None
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime)


class Logs(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    action: str
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    ticket_id: Optional[int] = Field(default=None, foreign_key="tickets.id")
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime)