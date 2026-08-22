"""
Phase 9: expiry handling.

No background scheduler yet (kept simple for the prototype, per the doc).
expire_consents() is called on-demand from an endpoint; wire it to a
scheduler later without changing this function.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from .. import models


def expire_consents(db: Session) -> list[str]:
    """Flips ACTIVE consents whose expires_at has passed to EXPIRED.
    Returns the list of consent_ids that were changed."""
    now = datetime.utcnow()
    candidates = (
        db.query(models.Consent)
        .filter(
            models.Consent.status == models.ConsentStatus.ACTIVE,
            models.Consent.expires_at.isnot(None),
            models.Consent.expires_at < now,
        )
        .all()
    )

    changed_ids = []
    for consent in candidates:
        consent.status = models.ConsentStatus.EXPIRED
        changed_ids.append(consent.consent_id)

    if changed_ids:
        db.commit()

    return changed_ids
