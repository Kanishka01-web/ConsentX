def _create_and_activate(client, principal, purpose="Loan eligibility check", data_type="Bank transaction data", expires_at=None):
    payload = {"user_id": principal["user_id"], "purpose": purpose, "data_type": data_type}
    if expires_at:
        payload["expires_at"] = expires_at
    create = client.post("/consent/", headers=principal["headers"], json=payload)
    consent_id = create.json()["consent_id"]
    client.patch(f"/consent/{consent_id}/activate", json={"blockchain_tx_hash": "0xtest"})
    return consent_id


def test_access_denied_when_pending(client, principal, fiduciary):
    create = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"], "purpose": "Loan check", "data_type": "Bank data",
    })
    consent_id = create.json()["consent_id"]

    r = client.post("/access/request", headers=fiduciary["headers"], json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Loan check", "requested_data_type": "Bank data",
    })
    assert r.status_code == 403
    assert "PENDING" in r.json()["detail"]


def test_access_allowed_when_active_and_matching(client, principal, fiduciary):
    consent_id = _create_and_activate(client, principal)

    r = client.post("/access/request", headers=fiduciary["headers"], json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Loan eligibility check", "requested_data_type": "Bank transaction data",
    })
    assert r.status_code == 200
    assert r.json()["allowed"] is True


def test_access_denied_when_revoked(client, principal, fiduciary):
    consent_id = _create_and_activate(client, principal)
    client.post(f"/consent/{consent_id}/revoke", headers=principal["headers"])

    r = client.post("/access/request", headers=fiduciary["headers"], json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Loan eligibility check", "requested_data_type": "Bank transaction data",
    })
    assert r.status_code == 403
    assert "REVOKED" in r.json()["detail"]


def test_access_denied_when_expired(client, principal, fiduciary):
    consent_id = _create_and_activate(client, principal, expires_at="2020-01-01T00:00:00")
    client.post("/consent/expire-check")

    r = client.post("/access/request", headers=fiduciary["headers"], json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Loan eligibility check", "requested_data_type": "Bank transaction data",
    })
    assert r.status_code == 403
    assert "expired" in r.json()["detail"].lower()


def test_access_denied_on_wrong_purpose(client, principal, fiduciary):
    consent_id = _create_and_activate(client, principal)

    r = client.post("/access/request", headers=fiduciary["headers"], json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Marketing outreach", "requested_data_type": "Bank transaction data",
    })
    assert r.status_code == 403
    assert "purpose" in r.json()["detail"].lower()


def test_access_denied_on_wrong_data_type(client, principal, fiduciary):
    consent_id = _create_and_activate(client, principal)

    r = client.post("/access/request", headers=fiduciary["headers"], json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Loan eligibility check", "requested_data_type": "Credit score history",
    })
    assert r.status_code == 403
    assert "scope" in r.json()["detail"].lower()


def test_principal_cannot_request_access(client, principal, fiduciary):
    consent_id = _create_and_activate(client, principal)

    r = client.post("/access/request", headers=principal["headers"], json={
        "consent_id": consent_id, "accessor_id": "self",
        "requested_purpose": "Loan eligibility check", "requested_data_type": "Bank transaction data",
    })
    assert r.status_code == 403


def test_access_request_requires_auth(client, principal):
    consent_id = _create_and_activate(client, principal)

    r = client.post("/access/request", json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Loan eligibility check", "requested_data_type": "Bank transaction data",
    })
    assert r.status_code == 401