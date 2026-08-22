def test_create_consent_requires_auth(client):
    r = client.post("/consent/", json={
        "user_id": "someone", "purpose": "Loan check", "data_type": "Bank data",
    })
    assert r.status_code == 401


def test_create_consent_starts_pending(client, principal):
    r = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"],
        "purpose": "Loan eligibility check",
        "data_type": "Bank transaction data",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "PENDING"
    assert body["ai_risk"] is not None


def test_activate_consent(client, principal):
    create = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"], "purpose": "Loan check", "data_type": "Bank data",
    })
    consent_id = create.json()["consent_id"]

    r = client.patch(f"/consent/{consent_id}/activate", json={"blockchain_tx_hash": "0xtest"})
    assert r.status_code == 200
    assert r.json()["status"] == "ACTIVE"
    assert r.json()["blockchain_tx_hash"] == "0xtest"


def test_cannot_activate_twice(client, principal):
    create = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"], "purpose": "Loan check", "data_type": "Bank data",
    })
    consent_id = create.json()["consent_id"]
    client.patch(f"/consent/{consent_id}/activate", json={"blockchain_tx_hash": "0xtest"})

    r = client.patch(f"/consent/{consent_id}/activate", json={"blockchain_tx_hash": "0xagain"})
    assert r.status_code == 400


def test_revoke_requires_active_status(client, principal):
    create = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"], "purpose": "Loan check", "data_type": "Bank data",
    })
    consent_id = create.json()["consent_id"]

    # still PENDING - revoke should fail
    r = client.post(f"/consent/{consent_id}/revoke", headers=principal["headers"])
    assert r.status_code == 400

    client.patch(f"/consent/{consent_id}/activate", json={"blockchain_tx_hash": "0xtest"})
    r2 = client.post(f"/consent/{consent_id}/revoke", headers=principal["headers"])
    assert r2.status_code == 200
    assert r2.json()["status"] == "REVOKED"


def test_expire_check_flips_expired_consents(client, principal):
    create = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"], "purpose": "Loan check", "data_type": "Bank data",
        "expires_at": "2020-01-01T00:00:00",
    })
    consent_id = create.json()["consent_id"]
    client.patch(f"/consent/{consent_id}/activate", json={"blockchain_tx_hash": "0xtest"})

    r = client.post("/consent/expire-check")
    assert r.status_code == 200
    assert consent_id in r.json()["expired_consent_ids"]

    check = client.get(f"/consent/{consent_id}")
    assert check.json()["status"] == "EXPIRED"