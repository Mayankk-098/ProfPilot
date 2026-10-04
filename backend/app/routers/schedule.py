from datetime import date as Date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.schemas.academic import ScheduleResponse
from app.schemas.schedule import (
    CancelClassRequest,
    RescheduleClassRequest,
    ScheduleChangeResponse,
)
from app.services import schedule_service
from app.services import clock
from app.services.auth_service import get_current_user


router = APIRouter(
    prefix="/schedule",
    tags=["Schedule"],
)


def _hhmm(value):
    return value.strftime("%H:%M") if value else None


def _change_response(change) -> ScheduleChangeResponse:
    return ScheduleChangeResponse(
        item_id=change.item_id,
        on_date=change.on_date.isoformat(),
        status=change.status,
        new_date=(
            change.new_date.isoformat()
            if change.new_date
            else None
        ),
        new_start_time=_hhmm(change.new_start_time),
        new_end_time=_hhmm(change.new_end_time),
        new_room=change.new_room,
        reason=change.reason,
    )


@router.get(
    "/",
    response_model=list[ScheduleResponse],
)
def get_schedule(
    on: Date | None = Query(
        default=None,
        alias="date",
    ),
    include_cancelled: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    day = on or clock.today()

    return schedule_service.day_schedule(
        db,
        day,
        lecturer_id=current_user.lecturer_id,
        include_cancelled=include_cancelled,
    )


@router.get(
    "/upcoming",
    response_model=list[ScheduleResponse],
)
def get_upcoming(
    days: int = Query(
        default=7,
        ge=1,
        le=60,
    ),
    include_cancelled: bool = False,
    at: datetime | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return schedule_service.upcoming(
        db,
        at or clock.now(),
        days=days,
        lecturer_id=current_user.lecturer_id,
        include_cancelled=include_cancelled,
    )


@router.get(
    "/next",
    response_model=ScheduleResponse | None,
)
def get_next_class(
    at: datetime | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return schedule_service.next_class(
        db,
        at or clock.now(),
        lecturer_id=current_user.lecturer_id,
    )


@router.post(
    "/{item_id}/cancel",
    response_model=ScheduleChangeResponse,
)
def cancel_class(
    item_id: str,
    request: CancelClassRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        change = schedule_service.cancel_class(
            db,
            item_id,
            request.on_date,
            request.reason,
            lecturer_id=current_user.lecturer_id,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return _change_response(change)


@router.post(
    "/{item_id}/reschedule",
    response_model=ScheduleChangeResponse,
)
def reschedule_class(
    item_id: str,
    request: RescheduleClassRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        change = schedule_service.reschedule_class(
            db,
            item_id,
            request.on_date,
            request.new_date,
            request.new_start_time,
            request.new_end_time,
            request.new_room,
            request.reason,
            lecturer_id=current_user.lecturer_id,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    return _change_response(change)


@router.delete(
    "/{item_id}/changes/{on_date}",
    status_code=204,
)
def restore_class(
    item_id: str,
    on_date: Date,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        schedule_service.restore_class(
            db,
            item_id,
            on_date,
            lecturer_id=current_user.lecturer_id,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error
