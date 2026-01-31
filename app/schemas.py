# app/schemas.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

#region === IN ===
# --- All ---
class AdminAllIn(BaseModel):
    class Config:
        from_attributes = True
        orm_mode = True

# --- Course ---
# class CourseIn(BaseModel):
    # id: int
    # name: str
    # weekday: int
    # start_time: str  # оставляем str для API
    # end_time: str
    # slot_range: int

    # class Config:
    #     from_attributes = True
    #     orm_mode = True

# --- Delete ---
class AdminDeleteIn(BaseModel):
    user_ids: Optional[List[int]] = Field(default=None, description="Delete users by ID (-1 for all)")
    course_ids: Optional[List[int]]  = Field(default=None, description="(Not in use!) Delete courses by ID (-1 for all)")
    ticket_type_ids: Optional[List[int]] = Field(default=None, description="Delete ticket types by ID (-1 for all)")
    ticket_ids: Optional[List[int]] = Field(default=None, description="Delete tickets by ID (-1 for all)")

    class Config:
        from_attributes = True
        orm_mode = True

# --- Reset ---
class AdminResetIn(BaseModel):
    class Config:
        from_attributes = True
        orm_mode = True

# --- Ticket ---
class AdminTicketIn(BaseModel):
    id: Optional[int]
    name: Optional[str] = Field(..., example="Disaply name of the ticket")
    status: Optional[str] = Field(..., example="active/closed/deleted")
    timestamp: Optional[datetime] = Field(default=None, example="(2023-01-20T16:10:00) Required only for type debt")
    created_at: Optional[datetime] = Field(..., example="Automatically set by the server")
    user_id: Optional[int] = Field(..., example="ID of the user to connect the ticket to")
    ticket_type_id: Optional[int] = Field(..., example="ID of the ticket type")

    class Config:
        from_attributes = True
        orm_mode = True

# --- Ticket Type ---
class AdminTicketTypeIn(BaseModel):
    id: Optional[int]
    name: str = Field(..., example="Name of the ticket type, used in requests/code")
    title: Optional[str] = Field(default=None, example="Display title of the ticket type, will be created of name field")
    max_per_user: Optional[int] = Field(..., example="Maximum number of tickets per user")
    require_time: Optional[int] = Field(default=None, example="(0/1) Does this type require time?")
    symbol: Optional[str]  = Field(default=None, example="(Ё) Display symbol of the ticket type, will be created of first letter of name field")

    class Config:
        from_attributes = True
        orm_mode = True

# --- User ---
class AdminUserIn(BaseModel):
    id: Optional[int] = Field(default=None, example="ID of the user")
    tg_id: Optional[str] = Field(default=None, example="Telegram ID of the user")
    debt_streak: int = Field(..., example="(0/1/2) Debt streak of the user")
    name: str = Field(..., example="Display name of the user")
    course_id: Optional[int] = Field(default=None, example="(Not in use!) ID of the course to which the user belongs")

    class Config:
        from_attributes = True
        orm_mode = True

# --- Book ---
class UserBookIn(BaseModel):
    type: str = Field(..., example="Type of the ticket to book")
    id: Optional[int] = Field(default=None, example="(tg_id can be used instead) ID of the user to connect the ticket to")
    tg_id: Optional[int] = Field(default=None, example="(id can be used instead) Telegram ID of the user to connect the ticket to")
    timestamp: Optional[datetime] = Field(default=None, example="(2023-01-20T16:10:00) Timestamp for redo. +Timestamp required only for type debt")

    class Config:
        from_attributes = True
        orm_mode = True

# --- Cancel ---
class UserCancelIn(BaseModel):
    id: Optional[int] = Field(default=None, example="ID of the ticket to cancel (can be get from /status)")

    class Config:
        from_attributes = True
        orm_mode = True

# --- Timeslots / Dates ---
class UserTimeslotsIn(BaseModel):
    class Config:
        from_attributes = True
        orm_mode = True

# --- Status ---
class UserStatusIn(BaseModel):
    id: Optional[int] = Field(default=None, example="(tg_id can be get used instead) ID of the user to get status")
    tg_id: Optional[int] = Field(default=None, example="(id can be get used instead) Telegram ID of the user to get status")

    class Config:
        from_attributes = True
        orm_mode = True

# --- UserTypesIn ---
class UserTypesIn(BaseModel):
    class Config:
        from_attributes = True
        orm_mode = True
#endregion
#region === OUT ===
# --- All ---