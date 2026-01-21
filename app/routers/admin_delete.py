from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User, Course, TicketType, Ticket, course_tickettype

router = APIRouter()

@router.delete("/")
def delete_bulk(
    user_ids: list[int] | None = Query(None, description="Delete users by ID (-1 for all)"),
    course_ids: list[int] | None = Query(None, description="Delete specific courses by ID (-1 for all)"),
    ticket_type_ids: list[int] | None = Query(None, description="Delete specific ticket types by ID (-1 for all)"),
    ticket_ids: list[int] | None = Query(None, description="Delete specific tickets by ID (-1 for all)"),
    db: Session = Depends(get_db),
):
    try:
        # tickets (явное удаление)
        if ticket_ids:
            if ticket_ids[0] == -1:  # special case: delete all tickets
                db.query(Ticket).delete(synchronize_session=False)
            db.query(Ticket)\
              .filter(Ticket.id.in_(ticket_ids))\
              .delete(synchronize_session=False)

        # ticket types
        if ticket_type_ids:
            if ticket_type_ids[0] == -1:  # special case: delete all ticket types
                ticket_type_ids = [tt.id for tt in db.query(TicketType.id).all()]
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
            if user_ids[0] == -1:  # special case: delete all users
                user_ids = [u.id for u in db.query(User.id).all()]
            db.query(Ticket)\
              .filter(Ticket.user_id.in_(user_ids))\
              .delete(synchronize_session=False)

            db.query(User)\
              .filter(User.id.in_(user_ids))\
              .delete(synchronize_session=False)

        # courses
        if course_ids:
            if course_ids[0] == -1:  # special case: delete all courses
                course_ids = [c.id for c in db.query(Course.id).all()]
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
        return {"status": "success", "message": "Deletion completed successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during deletion: {str(e)}")