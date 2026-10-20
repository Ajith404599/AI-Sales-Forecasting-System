def test_get_profile(client, staff_token):
    response = client.get("/profile", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "test_staff"
    assert data["email"] == "staff@test.com"


def test_update_profile_email(client, staff_token):
    response = client.put("/profile", json={"email": "newstaffemail@test.com"}, headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "newstaffemail@test.com"


def test_update_profile_password(client, staff_token):
    # Try with wrong current password
    fail_res = client.put(
        "/profile",
        json={"current_password": "wrongpassword", "new_password": "newpassword123"},
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert fail_res.status_code == 400

    # Try with valid current password
    ok_res = client.put(
        "/profile",
        json={"current_password": "staff123", "new_password": "newpassword123"},
        headers={"Authorization": f"Bearer {staff_token}"}
    )
    assert ok_res.status_code == 200

    # Verify login with new password
    login_res = client.post("/auth/token", data={"username": "test_staff", "password": "newpassword123"})
    assert login_res.status_code == 200

    # Restore original password for fixture isolation
    restore_res = client.put(
        "/profile",
        json={"current_password": "newpassword123", "new_password": "staff123"},
        headers={"Authorization": f"Bearer {login_res.json()['access_token']}"}
    )
    assert restore_res.status_code == 200


def test_admin_list_users_forbidden_for_staff(client, staff_token):
    response = client.get("/users", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 403


def test_admin_list_users_success(client, admin_token):
    response = client.get("/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_admin_create_user(client, admin_token):
    payload = {
        "username": "new_created_user",
        "email": "created@test.com",
        "password": "createdpassword123",
        "role": "staff",
        "is_active": True
    }
    response = client.post("/users", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "new_created_user"
    assert data["role"] == "staff"


def test_admin_update_user(client, admin_token):
    payload = {
        "role": "manager",
        "is_active": True
    }
    response = client.put("/users/1", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "manager"
