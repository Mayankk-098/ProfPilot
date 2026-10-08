from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.auth_service import get_current_user
from app.services.risk_radar_service import build_risk_radar

router = APIRouter(
    prefix="/risk",
    tags=["Academic Risk"],
)


@router.get("/radar")
def get_risk_radar(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return build_risk_radar(
            db=db,
            lecturer_id=current_user.lecturer_id,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error
