def test_audit_logs_forbidden_for_staff(client, staff_token):
    response = client.get("/audit-logs", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 403


def test_audit_logs_allowed_for_manager(client, manager_token):
    response = client.get("/audit-logs", headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_audit_logs_filter_module(client, admin_token):
    response = client.get("/audit-logs?module=SYSTEM", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert all(item["module"] == "SYSTEM" for item in data)


def test_audit_log_details(client, admin_token):
    response = client.get("/audit-logs/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["log_id"] == 1


def test_audit_log_details_not_found(client, admin_token):
    response = client.get("/audit-logs/99999", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 404
