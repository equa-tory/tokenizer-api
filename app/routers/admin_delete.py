from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, Course, TicketType, Ticket, course_tickettype

router = APIRouter()

@router.delete("/")
def delete_bulk(
    user_ids: list[int] | None = Query(None, description="Удалить конкретных пользователей по ID"),
    course_ids: list[int] | None = Query(None, description="Удалить конкретные курсы по ID"),
    ticket_type_ids: list[int] | None = Query(None, description="Удалить конкретные типы билетов по ID"),
    ticket_ids: list[int] | None = Query(None, description="Удалить конкретные билеты по ID"),
    db: Session = Depends(get_db),
):
    try:
        # tickets (явное удаление)
        if ticket_ids:
            db.query(Ticket)\
              .filter(Ticket.id.in_(ticket_ids))\
              .delete(synchronize_session=False)

        # ticket types
        if ticket_type_ids:
            db.query(Ticket)\
              .filter(Ticket.ticket_type_id.in_(ticket_type_ids))\
              .delete(synchronize_session=False)

            db.execute(
                course_tickettype.delete().where(
                    course_tickettype.c.tickettype_id.in_(ticket_type_ids)
                )
            )

            db.query(TicketType)\
              .filter(TicketType.id.in_(ticket_type_ids))\
              .delete(synchronize_session=False)

        # users
        if user_ids:
            db.query(Ticket)\
              .filter(Ticket.user_id.in_(user_ids))\
              .delete(synchronize_session=False)

            db.query(User)\
              .filter(User.id.in_(user_ids))\
              .delete(synchronize_session=False)

        # courses
        if course_ids:
            db.execute(
                course_tickettype.delete().where(
                    course_tickettype.c.course_id.in_(course_ids)
                )
            )

            db.query(User)\
              .filter(User.course_id.in_(course_ids))\
              .update({User.course_id: None}, synchronize_session=False)

            db.query(Course)\
              .filter(Course.id.in_(course_ids))\
              .delete(synchronize_session=False)

        db.commit()
        return {"status": "success", "message": "Удаление выполнено!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении: {str(e)}")