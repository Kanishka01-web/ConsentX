from typing import List
from ..dependencies import get_current_user, require_data_fiduciary
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


# POST /audit/access
@router.post("/access", response_model=schemas.AccessLogOut)
def record_access(
    payload: schemas.AccessLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_data_fiduciary),
):
    consent = db.query(models.Consent).filter(models.Consent.consent_id == payload.consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")

    # Phase 12: revoked/expired/pending consent cannot authorize access.
    if consent.status != models.ConsentStatus.ACTIVE:
        raise HTTPException(
            status_code=403,
            detail=f"Consent status is {consent.status.value}; access is not authorized",
        )

    log = models.AccessLog(
        consent_id=payload.consent_id,
        accessor_id=payload.accessor_id,
        purpose=payload.purpose,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# GET /audit/{user_id}
# Returns the access history for every consent belonging to this user,
# so the frontend can show a single tamper-evident audit trail per user.
@router.get("/{user_id}", response_model=List[schemas.AccessLogOut])
def get_audit_history(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if current_user.role == models.UserRole.DATA_PRINCIPAL and current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="You can only view your own audit history")

    consent_ids = [
        c.consent_id
        for c in db.query(models.Consent).filter(models.Consent.user_id == user_id).all()
    ]
    if not consent_ids:
        return []

    return (
        db.query(models.AccessLog)
        .filter(models.AccessLog.consent_id.in_(consent_ids))
        .order_by(models.AccessLog.accessed_at.desc())
        .all()
    )