from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str