from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..services import blockchain_service

from ..database import get_db
from .. import models, schemas
from ..services.consent_service import validate_data_access
from ..dependencies import require_data_fiduciary

router = APIRouter(prefix="/access", tags=["Access"])


# POST /access/request
@router.post("/request", response_model=schemas.AccessRequestOut)
def request_access(
    payload: schemas.AccessRequestIn,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_data_fiduciary),
):
    consent = db.query(models.Consent).filter(models.Consent.consent_id == payload.consent_id).first()

    allowed, reason = validate_data_access(
        consent,
        payload.requested_purpose,
        payload.requested_data_type,
    )

    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    # Phase 17: allowed access gets logged for the audit trail.
    log = models.AccessLog(
        consent_id=payload.consent_id,
        accessor_id=payload.accessor_id,
        purpose=payload.requested_purpose,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Phase 22: try logging on-chain; falls back to DB-only logging until
    # Nirali's logAccess() is wired in.
    try:
        tx_hash = blockchain_service.log_access(payload.consent_id, payload.accessor_id)
        log.blockchain_tx_hash = tx_hash
        db.commit()
        db.refresh(log)
    except NotImplementedError:
        pass  # on-chain logging not wired yet; DB record already saved above

    return schemas.AccessRequestOut(allowed=True, reason=reason, access_log=log)