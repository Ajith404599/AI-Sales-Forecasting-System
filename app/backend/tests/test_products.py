def test_list_products_unauthorized(client):
    response = client.get("/products")
    assert response.status_code == 401


def test_list_products_as_staff(client, staff_token):
    response = client.get("/products", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3


def test_filter_products_by_category(client, staff_token):
    response = client.get("/products?category=Electronics", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert all(p["category"] == "Electronics" for p in data)


def test_filter_products_by_active_status(client, staff_token):
    response = client.get("/products?active_status=true", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert all(p["active_status"] is True for p in data)


def test_search_products(client, staff_token):
    response = client.get("/products?search=Keyboard", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Keyboard" in data[0]["product_name"]


def test_get_single_product(client, staff_token):
    response = client.get("/products/1", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    assert response.json()["product_id"] == 1


def test_get_single_product_not_found(client, staff_token):
    response = client.get("/products/9999", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 404


def test_create_product_forbidden_for_staff(client, staff_token):
    payload = {
        "product_name": "Unauthorized Tablet",
        "category": "Electronics",
        "base_price": 299.99,
        "description": "Staff trying to create",
        "active_status": True
    }
    response = client.post("/products", json=payload, headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 403


def test_create_product_as_manager(client, manager_token):
    payload = {
        "product_name": "Manager Created Headset",
        "category": "Audio",
        "base_price": 79.99,
        "description": "Created by manager",
        "active_status": True
    }
    response = client.post("/products", json=payload, headers={"Authorization": f"Bearer {manager_token}"})
    assert response.status_code == 201
    data = response.json()
    assert data["product_name"] == "Manager Created Headset"
    assert data["product_id"] is not None


def test_update_product_as_admin(client, admin_token):
    payload = {
        "product_name": "Updated Keyboard Title",
        "base_price": 89.99
    }
    response = client.put("/products/1", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["product_name"] == "Updated Keyboard Title"
    assert float(data["base_price"]) == 89.99


def test_soft_delete_product(client, admin_token, staff_token):
    response = client.delete("/products/1", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["active_status"] is False

    # Check that it is now inactive
    get_res = client.get("/products/1", headers={"Authorization": f"Bearer {staff_token}"})
    assert get_res.status_code == 200
    assert get_res.json()["active_status"] is False
