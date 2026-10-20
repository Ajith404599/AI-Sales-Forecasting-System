from datetime import datetime, timedelta


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_and_filter_sales(client, staff_token):
    response = client.post("/sales", json={
        "product_id": 2,
        "quantity": 3,
        "unit_price": 10.0,
        "discount_amount": 2.0,
        "sale_date": datetime.now().isoformat(),
    }, headers=_headers(staff_token))
    assert response.status_code == 201
    created = response.json()
    assert created["user_id"] == 3
    assert float(created["total_amount"]) == 28.0
    detail = client.get(f"/sales/{created['sale_id']}", headers=_headers(staff_token))
    assert detail.status_code == 200
    assert detail.json()["sale_id"] == created["sale_id"]

    filtered = client.get("/sales?product_id=2&search=Chair", headers=_headers(staff_token))
    assert filtered.status_code == 200
    assert any(sale["sale_id"] == created["sale_id"] for sale in filtered.json())


def test_sales_date_filter_and_invalid_range(client, staff_token):
    headers = _headers(staff_token)
    after_recent = (datetime.now() - timedelta(days=20)).isoformat()
    filtered = client.get(f"/sales?start_date={after_recent}", headers=headers)
    assert filtered.status_code == 200
    assert all(sale["sale_id"] != 2 for sale in filtered.json())

    invalid = client.get(
        f"/sales?start_date={datetime.now().isoformat()}&end_date={(datetime.now() - timedelta(days=1)).isoformat()}",
        headers=headers,
    )
    assert invalid.status_code == 400


def test_sale_update_permissions_and_recalculation(client, staff_token, manager_token):
    staff_headers = _headers(staff_token)
    forbidden = client.put("/sales/1", json={"quantity": 4}, headers=staff_headers)
    assert forbidden.status_code == 403

    own_sale = client.put("/sales/2", json={"quantity": 3, "unit_price": 10, "discount_amount": 5}, headers=staff_headers)
    assert own_sale.status_code == 200
    assert own_sale.json()["user_id"] == 3
    assert float(own_sale.json()["total_amount"]) == 25.0

    manager_sale = client.put("/sales/1", json={"quantity": 4}, headers=_headers(manager_token))
    assert manager_sale.status_code == 200
    assert manager_sale.json()["quantity"] == 4


def test_sale_delete_is_manager_or_admin_only(client, staff_token, manager_token):
    staff_sale = client.post("/sales", json={"product_id": 2, "quantity": 1}, headers=_headers(staff_token))
    assert staff_sale.status_code == 201
    sale_id = staff_sale.json()["sale_id"]

    denied = client.delete(f"/sales/{sale_id}", headers=_headers(staff_token))
    assert denied.status_code == 403

    deleted = client.delete(f"/sales/{sale_id}", headers=_headers(manager_token))
    assert deleted.status_code == 204
    assert client.get(f"/sales/{sale_id}", headers=_headers(manager_token)).status_code == 404