def test_register_user(client):
    r = client.post("/auth/register", json={
        "name": "Alice",
        "email": "alice@example.com",
        "password": "pass123",
        "role": "data_principal",
    })
    assert r.status_code == 200
    assert r.json()["role"] == "data_principal"


def test_register_duplicate_email_fails(client):
    body = {"name": "Bob", "email": "bob@example.com", "password": "pass123", "role": "data_principal"}
    r1 = client.post("/auth/register", json=body)
    assert r1.status_code == 200

    r2 = client.post("/auth/register", json=body)
    assert r2.status_code == 400


def test_login_wrong_password_fails(client):
    client.post("/auth/register", json={
        "name": "Carl", "email": "carl@example.com", "password": "correct", "role": "data_principal",
    })
    r = client.post("/auth/login", json={"email": "carl@example.com", "password": "wrong"})
    assert r.status_code == 401