from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..services import blockchain_service
from ..services.ai_service import analyze_consent_text
from ..services.consent_lifecycle import expire_consents

router = APIRouter(prefix="/consent", tags=["consent"])


# POST /consent
@router.post("/", response_model=schemas.ConsentOut)
def create_consent(
    payload: schemas.ConsentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Phase 11: run the AI analyzer at creation time. Falls back to
    # purpose + data_type if no raw consent_text was given.
    text_to_analyze = payload.consent_text or f"{payload.purpose} - {payload.data_type}"
    ai_result = analyze_consent_text(text_to_analyze)

    # A new consent starts PENDING until Nirali's blockchain layer confirms
    # it (PENDING -> ACTIVE happens via /activate below).
    consent = models.Consent(
        user_id=payload.user_id,
        purpose=payload.purpose,
        data_type=payload.data_type,
        status=models.ConsentStatus.PENDING,
        expires_at=payload.expires_at,
        ai_risk=ai_result["risk"],
        ai_reason=ai_result["reason"],
        ai_recommendation=ai_result["recommendation"],
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)
    return consent


# GET /consent/user/{user_id}
# NOTE: the doc listed this as GET /consent/{user_id}, but that collides with
# GET /consent/{consent_id} below (FastAPI can't tell a user_id from a
# consent_id in the same path slot), so it's namespaced under /user/ here.
@router.get("/user/{user_id}", response_model=List[schemas.ConsentOut])
def get_consents_for_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Consent).filter(models.Consent.user_id == user_id).all()


# GET /consent/{consent_id}
@router.get("/{consent_id}", response_model=schemas.ConsentOut)
def get_consent(consent_id: str, db: Session = Depends(get_db)):
    consent = db.query(models.Consent).filter(models.Consent.consent_id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")
    return consent


# PATCH /consent/{consent_id}/activate
# Called by the integration layer once Nirali's chain confirms the consent.
@router.patch("/{consent_id}/activate", response_model=schemas.ConsentOut)
def activate_consent(consent_id: str, payload: schemas.ConsentActivate, db: Session = Depends(get_db)):
    consent = db.query(models.Consent).filter(models.Consent.consent_id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")

    if consent.status != models.ConsentStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Cannot activate a consent with status {consent.status.value}")

    # Phase 20: try the real chain call first; fall back to the manually
    # supplied tx hash until Nirali's contract is wired in.
    try:
        tx_hash = blockchain_service.activate_consent(consent_id)
    except NotImplementedError:
        tx_hash = payload.blockchain_tx_hash

    consent.status = models.ConsentStatus.ACTIVE
    consent.blockchain_tx_hash = tx_hash
    db.commit()
    db.refresh(consent)
    return consent


# POST /consent/{consent_id}/revoke
@router.post("/{consent_id}/revoke", response_model=schemas.ConsentOut)
def revoke_consent(
    consent_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    consent = db.query(models.Consent).filter(models.Consent.consent_id == consent_id).first()
    if not consent:
        raise HTTPException(status_code=404, detail="Consent record not found")

    # A data_principal can only revoke their own consent.
    if current_user.role == models.UserRole.DATA_PRINCIPAL and consent.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You can only revoke your own consent")

    # Phase 8: only an ACTIVE consent can be revoked.
    if consent.status != models.ConsentStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Cannot revoke a consent with status {consent.status.value}")

    # Phase 21: same fallback pattern as activate.
    try:
        blockchain_service.revoke_consent(consent_id)
    except NotImplementedError:
        pass  # on-chain revoke not wired yet; DB-level revoke still happens

    consent.status = models.ConsentStatus.REVOKED
    consent.revoked_at = datetime.utcnow()
    db.commit()
    db.refresh(consent)
    return consent


# POST /consent/expire-check
# Phase 9: on-demand trigger for ACTIVE -> EXPIRED. Call this from a
# scheduler later; kept manual for now to keep the prototype testable.
@router.post("/expire-check")
def run_expiry_check(db: Session = Depends(get_db)):
    expired_ids = expire_consents(db)
    return {"expired_consent_ids": expired_ids, "count": len(expired_ids)}