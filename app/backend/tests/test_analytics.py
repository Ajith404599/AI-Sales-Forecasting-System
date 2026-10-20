def test_analytics_summary(client, staff_token):
    response = client.get("/analytics/summary", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert "total_sales_count" in data
    assert "total_revenue" in data
    assert "total_quantity_sold" in data
    assert "average_order_value" in data
    assert "active_products_count" in data
    assert data["total_sales_count"] >= 2
    assert data["total_revenue"] > 0


def test_analytics_monthly(client, staff_token):
    response = client.get("/analytics/monthly", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "month" in item
    assert "total_orders" in item
    assert "total_revenue" in item


def test_analytics_products(client, staff_token):
    response = client.get("/analytics/products?sort_by=revenue_desc&limit=10", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "total_revenue" in data[0]
    assert "total_quantity_sold" in data[0]


def test_analytics_categories(client, staff_token):
    response = client.get("/analytics/categories", headers={"Authorization": f"Bearer {staff_token}"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "category" in data[0]
    assert "total_revenue" in data[0]
