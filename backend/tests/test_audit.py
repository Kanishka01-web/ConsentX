def test_successful_access_creates_audit_record(client, principal, fiduciary):
    create = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"], "purpose": "Loan check", "data_type": "Bank data",
    })
    consent_id = create.json()["consent_id"]
    client.patch(f"/consent/{consent_id}/activate", json={"blockchain_tx_hash": "0xtest"})

    client.post("/access/request", headers=fiduciary["headers"], json={
        "consent_id": consent_id, "accessor_id": "bank1",
        "requested_purpose": "Loan check", "requested_data_type": "Bank data",
    })

    r = client.get(f"/audit/{principal['user_id']}", headers=principal["headers"])
    assert r.status_code == 200
    logs = r.json()
    assert len(logs) == 1
    assert logs[0]["consent_id"] == consent_id


def test_principal_cannot_view_others_audit_history(client, principal, fiduciary):
    r = client.get(f"/audit/{fiduciary['user_id']}", headers=principal["headers"])
    assert r.status_code == 403


def test_audit_history_requires_auth(client, principal):
    r = client.get(f"/audit/{principal['user_id']}")
    assert r.status_code == 401