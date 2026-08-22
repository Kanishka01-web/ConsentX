from datetime import datetime, timezone


def validate_data_access(
    consent,
    requested_purpose: str,
    requested_data_type: str,
):
    """
    Validate whether a consent permits a requested data access.
    """

    # 1. Consent must exist
    if consent is None:
        return False, "Consent not found"

    # 2. Consent must be ACTIVE
    if consent.status.value != "ACTIVE":
        return False, f"Consent is {consent.status.value}"

    # 3. Consent must not be expired
    if consent.expires_at:
        now = datetime.now(timezone.utc)

        expires_at = consent.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            return False, "Consent has expired"

    # 4. Purpose must match
    if consent.purpose.lower() != requested_purpose.lower():
        return False, "Requested purpose does not match consent purpose"

    # 5. Data type must match
    if consent.data_type.lower() != requested_data_type.lower():
        return False, "Requested data type is outside consent scope"

    return True, "Access allowed"