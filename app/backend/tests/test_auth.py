from datetime import datetime, timedelta, timezone
from jose import jwt

from app.core.security import create_access_token
from app.models.auth_session import AuthSession
from app.models.user import User


def test_login_success(client):
    response = client.post("/auth/token", data={"username": "test_admin", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "test_admin"
    assert data["user"]["role"] == "admin"
    claims = jwt.get_unverified_claims(data["access_token"])
    assert claims["exp"] - claims["iat"] == 15 * 60


def test_successful_login_records_matching_session_timestamps(client, db_session):
    registered = client.post("/auth/register", json={
        "username": "history_login_user",
        "email": "history_login@test.com",
        "password": "history-password-123",
    })
    assert registered.status_code == 201
    login = client.post("/auth/token", data={
        "username": "history_login_user",
        "password": "history-password-123",
    })
    assert login.status_code == 200
    claims = jwt.get_unverified_claims(login.json()["access_token"])
    history_row = db_session.query(AuthSession).filter(
        AuthSession.auth_session_id == claims["auth_session_id"],
    ).one()
    login_at = history_row.login_at.replace(tzinfo=timezone.utc).timestamp()
    expires_at = history_row.session_expires_at.replace(tzinfo=timezone.utc).timestamp()
    assert abs(login_at - claims["iat"]) < 2
    assert abs(expires_at - claims["exp"]) < 2
    assert history_row.logout_at is None

    history = client.get("/auth/history", headers={
        "Authorization": f"Bearer {login.json()['access_token']}"
    })
    assert history.status_code == 200
    assert any(row["auth_session_id"] == claims["auth_session_id"] for row in history.json())


def test_login_with_email(client):
    response = client.post("/auth/token", data={"username": "manager@test.com", "password": "manager123"})
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "test_manager"
    assert data["user"]["role"] == "manager"


def test_login_wrong_password(client):
    response = client.post("/auth/token", data={"username": "test_admin", "password": "wrongpassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid password. 2 attempts remaining."


def test_login_unknown_user(client):
    response = client.post("/auth/token", data={"username": "nonexistent_user", "password": "any"})
    assert response.status_code == 401


def test_login_inactive_user(client):
    response = client.post("/auth/token", data={"username": "test_inactive", "password": "inactive123"})
    assert response.status_code == 403
    assert "Account is inactive" in response.json()["detail"]


def test_public_signup_defaults_to_analyst_and_rejects_duplicates(client):
    payload = {
        "username": "public_analyst",
        "full_name": "Public Analyst",
        "email": "public_analyst@test.com",
        "password": "analyst-password-123",
        "role": "admin",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "analyst"
    assert response.json()["user"]["full_name"] == "Public Analyst"

    duplicate = client.post("/auth/register", json=payload)
    assert duplicate.status_code == 409

    duplicate_email = client.post("/auth/register", json={
        "username": "another_analyst",
        "email": payload["email"],
        "password": "another-password-123",
    })
    assert duplicate_email.status_code == 409


def test_failed_login_attempts_lock_account(client):
    registered = client.post("/auth/register", json={
        "username": "lockout_user",
        "email": "lockout@test.com",
        "password": "correct-password-123",
    })
    assert registered.status_code == 201

    first = client.post("/auth/token", data={"username": "lockout_user", "password": "wrong"})
    second = client.post("/auth/token", data={"username": "lockout_user", "password": "wrong"})
    third = client.post("/auth/token", data={"username": "lockout_user", "password": "wrong"})

    assert first.status_code == 401
    assert first.json()["detail"] == "Invalid password. 2 attempts remaining."
    assert second.status_code == 401
    assert second.json()["detail"] == "Invalid password. 1 attempt remaining."
    assert third.status_code == 423
    assert third.json()["detail"].startswith(
        "Maximum login attempts reached. Your account is temporarily locked."
    )
    assert "Try again in 14 minutes" in third.json()["detail"] or "Try again in 15 minutes" in third.json()["detail"]

    locked_login = client.post("/auth/token", data={
        "username": "lockout_user",
        "password": "correct-password-123",
    })
    assert locked_login.status_code == 423
    assert locked_login.json()["detail"].startswith(
        "Maximum login attempts reached. Your account is temporarily locked. Try again in "
    )


def test_correct_password_works_after_lock_expiry(client, db_session):
    registered = client.post("/auth/register", json={
        "username": "expired_lock_user",
        "email": "expired_lock@test.com",
        "password": "correct-password-123",
    })
    assert registered.status_code == 201
    for _ in range(3):
        client.post("/auth/token", data={"username": "expired_lock_user", "password": "wrong"})

    user = db_session.query(User).filter(User.username == "expired_lock_user").one()
    user.locked_until = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    successful = client.post("/auth/token", data={
        "username": "expired_lock_user",
        "password": "correct-password-123",
    })
    assert successful.status_code == 200
    db_session.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


def test_logout_revokes_tokens_and_closes_session(client, db_session):
    registered = client.post("/auth/register", json={
        "username": "logout_user",
        "email": "logout@test.com",
        "password": "logout-password-123",
    })
    assert registered.status_code == 201
    tokens = registered.json()
    claims = jwt.get_unverified_claims(tokens["access_token"])
    auth_session = db_session.query(AuthSession).filter(
        AuthSession.auth_session_id == claims["auth_session_id"]
    ).one()
    assert auth_session.login_at is not None
    assert auth_session.logout_at is None
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert client.get("/profile", headers=headers).status_code == 200

    logout_response = client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == 200
    assert client.get("/profile", headers=headers).status_code == 401
    assert client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]}).status_code == 401
    db_session.refresh(auth_session)
    assert auth_session.logout_at is not None
    assert auth_session.logout_reason == "manual"

    second_login = client.post("/auth/token", data={
        "username": "logout_user",
        "password": "logout-password-123",
    })
    assert second_login.status_code == 200
    second_claims = jwt.get_unverified_claims(second_login.json()["access_token"])
    assert second_claims["auth_session_id"] != claims["auth_session_id"]


def test_login_history_is_scoped_to_authenticated_user(client, admin_token, staff_token):
    admin_history = client.get("/auth/history", headers={"Authorization": f"Bearer {admin_token}"})
    staff_history = client.get("/auth/history?user_id=1", headers={"Authorization": f"Bearer {staff_token}"})
    assert admin_history.status_code == 200
    assert staff_history.status_code == 200
    assert admin_history.json()
    assert staff_history.json()
    assert all(item["user_id"] == 1 for item in admin_history.json())
    assert all(item["user_id"] == 3 for item in staff_history.json())


def test_refresh_never_extends_absolute_session_expiry(client, db_session):
    registered = client.post("/auth/register", json={
        "username": "refresh_session_user",
        "email": "refresh_session@test.com",
        "password": "refresh-session-password-123",
    })
    assert registered.status_code == 201
    original = registered.json()
    original_claims = jwt.get_unverified_claims(original["access_token"])

    refreshed = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert refreshed.status_code == 200
    refreshed_claims = jwt.get_unverified_claims(refreshed.json()["access_token"])
    assert refreshed_claims["exp"] <= original_claims["exp"]

    session = db_session.query(AuthSession).filter(
        AuthSession.auth_session_id == original_claims["auth_session_id"]
    ).one()
    assert session.session_expires_at.replace(tzinfo=timezone.utc).timestamp() == original_claims["exp"]

    session.session_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()
    rejected = client.post("/auth/refresh", json={"refresh_token": original["refresh_token"]})
    assert rejected.status_code == 401
    db_session.refresh(session)
    assert session.logout_reason == "expired"
    assert session.logout_at is not None


def test_expired_session_endpoint_records_logout_time(client, db_session):
    registered = client.post("/auth/register", json={
        "username": "auto_expiry_user",
        "email": "auto_expiry@test.com",
        "password": "auto-expiry-password-123",
    })
    assert registered.status_code == 201
    claims = jwt.get_unverified_claims(registered.json()["access_token"])
    auth_session = db_session.query(AuthSession).filter(
        AuthSession.auth_session_id == claims["auth_session_id"]
    ).one()
    auth_session.session_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    db_session.commit()

    expired_token = create_access_token(
        {key: value for key, value in claims.items() if key not in {"exp", "iat", "token_type"}},
        expires_delta=timedelta(seconds=-1),
    )
    response = client.post(
        "/auth/session-expired",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 200
    db_session.refresh(auth_session)
    assert auth_session.logout_at == auth_session.session_expires_at
    assert auth_session.logout_reason == "expired"


def test_successful_login_resets_failures_and_stores_last_login(client, db_session):
    registered = client.post("/auth/register", json={
        "username": "login_state_user",
        "email": "login_state@test.com",
        "password": "login-state-password-123",
    })
    assert registered.status_code == 201

    failed = client.post("/auth/token", data={"username": "login_state_user", "password": "wrong"})
    assert failed.status_code == 401
    successful = client.post("/auth/token", data={
        "username": "login_state_user",
        "password": "login-state-password-123",
    })
    assert successful.status_code == 200

    user = db_session.query(User).filter(User.username == "login_state_user").one()
    assert user.failed_login_attempts == 0
    assert user.locked_until is None
    assert user.last_login_at is not None
    assert successful.json()["user"]["last_login_at"] is not None

    next_failure = client.post("/auth/token", data={"username": "login_state_user", "password": "wrong"})
    assert next_failure.status_code == 401
    assert next_failure.json()["detail"] == "Invalid password. 2 attempts remaining."
