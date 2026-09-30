from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.academic import ScheduleItem
from app.schemas.academic import ScheduleResponse


router = APIRouter(
    prefix="/schedule",
    tags=["Schedule"],
)


@router.get("/", response_model=list[ScheduleResponse])
def get_schedule(
    db: Session = Depends(get_db),
):
    items = (
        db.query(ScheduleItem)
        .order_by(
            ScheduleItem.period,
            ScheduleItem.time,
        )
        .all()
    )

    return [
        ScheduleResponse(
            id=item.id,
            subject=item.subject,
            code=item.code,
            batch=item.batch,
            time=item.time,
            period=item.period,
            room=item.room,
            item_type=item.item_type,
            course_id=item.course_id,
        )
        for item in items
    ]