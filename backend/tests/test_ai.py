def test_ai_low_risk(client):
    r = client.post("/ai/analyze", json={
        "text": "We collect your account number only to process this loan application. Data is retained for 90 days.",
    })
    assert r.status_code == 200
    assert r.json()["risk"] == "Low"


def test_ai_high_risk(client):
    r = client.post("/ai/analyze", json={
        "text": "We may sell your financial data to third parties and retain it indefinitely.",
    })
    assert r.status_code == 200
    assert r.json()["risk"] == "High"


def test_consent_creation_stores_ai_result(client, principal):
    r = client.post("/consent/", headers=principal["headers"], json={
        "user_id": principal["user_id"],
        "purpose": "Loan check",
        "data_type": "Bank data",
        "consent_text": "We may sell your financial data to third parties and retain it indefinitely.",
    })
    assert r.json()["ai_risk"] == "High"