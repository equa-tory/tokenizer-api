from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, DateTime, Table, BigInteger, JSON
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
from typing import Optional

Base = declarative_base()

# Промежуточная таблица для связи Course <-> TicketType
course_tickettype = Table(
    "course_tickettype",
    Base.metadata,
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
    Column("tickettype_id", Integer, ForeignKey("tickettypes.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tg_id: Optional[int] = Column(BigInteger, unique=True, nullable=True)
    name = Column(String, nullable=False)

    tickets = relationship("Ticket", back_populates="user")
    course_id = Column(Integer, ForeignKey("courses.id"))
    course = relationship("Course", back_populates="users")
    debt_streak = Column(Integer, default=0)


class TicketType(Base):
    __tablename__ = "tickettypes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    max_per_day = Column(Integer, nullable=False)
    require_time = Column(Integer, nullable=True)  # В минутах или часах
    symbol = Column(String(1), nullable=True)

    courses = relationship("Course", secondary=course_tickettype, back_populates="ticket_types")
    tickets = relationship("Ticket", back_populates="ticket_type")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    weekday = Column(Integer, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_range = Column(Integer, nullable=False)

    ticket_types = relationship("TicketType", secondary=course_tickettype, back_populates="courses")
    users = relationship("User", back_populates="course")


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    number = Column(Integer, nullable=False)
    status = Column(String, default="active")
    timestamp = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="tickets")

    ticket_type_id = Column(Integer, ForeignKey("tickettypes.id"))
    ticket_type = relationship("TicketType", back_populates="tickets")

class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    kind = Column(String, nullable=False)  # http | action
    action = Column(String, nullable=False)

    # user_id = Column(Integer, nullable=True)
    status_code = Column(Integer, nullable=True)

    data = Column(JSON)        # input / meta
    created_at = Column(DateTime, default=datetime.utcnow)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)