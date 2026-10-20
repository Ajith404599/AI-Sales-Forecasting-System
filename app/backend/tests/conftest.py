import os
import sys
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend root is in sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.sale import Sale
from app.models.audit import AuditLog
from app.main import app

# Test in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # 1. Seed Users
    admin = User(
        username="test_admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        is_active=True
    )
    manager = User(
        username="test_manager",
        email="manager@test.com",
        hashed_password=get_password_hash("manager123"),
        role=UserRole.MANAGER,
        is_active=True
    )
    staff = User(
        username="test_staff",
        email="staff@test.com",
        hashed_password=get_password_hash("staff123"),
        role=UserRole.STAFF,
        is_active=True
    )
    inactive_user = User(
        username="test_inactive",
        email="inactive@test.com",
        hashed_password=get_password_hash("inactive123"),
        role=UserRole.STAFF,
        is_active=False
    )
    db.add_all([admin, manager, staff, inactive_user])
    db.commit()

    # 2. Seed Products
    p1 = Product(
        product_name="Pro Mechanical Keyboard",
        category="Electronics",
        base_price=99.99,
        description="RGB Wireless Mechanical Keyboard",
        active_status=True
    )
    p2 = Product(
        product_name="Ergo Office Chair",
        category="Furniture",
        base_price=249.50,
        description="High-back mesh chair",
        active_status=True
    )
    p3 = Product(
        product_name="Discontinued Mousepad",
        category="Accessories",
        base_price=15.00,
        description="Old edition mousepad",
        active_status=False
    )
    db.add_all([p1, p2, p3])
    db.commit()

    # 3. Seed Sales
    now = datetime.now()
    s1 = Sale(
        product_id=p1.product_id,
        user_id=admin.user_id,
        quantity=2,
        unit_price=99.99,
        discount_amount=0.00,
        total_amount=199.98,
        sale_date=now - timedelta(days=10)
    )
    s2 = Sale(
        product_id=p2.product_id,
        user_id=staff.user_id,
        quantity=1,
        unit_price=249.50,
        discount_amount=24.50,
        total_amount=225.00,
        sale_date=now - timedelta(days=40)
    )
    db.add_all([s1, s2])
    db.commit()

    # 4. Seed Audit Log
    log = AuditLog(
        user_id=admin.user_id,
        action="TEST_INIT",
        module="SYSTEM",
        description="Staging test database initialized."
    )
    db.add(log)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_token(client):
    res = client.post("/auth/token", data={"username": "test_admin", "password": "admin123"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def manager_token(client):
    res = client.post("/auth/token", data={"username": "test_manager", "password": "manager123"})
    assert res.status_code == 200
    return res.json()["access_token"]


@pytest.fixture
def staff_token(client):
    res = client.post("/auth/token", data={"username": "test_staff", "password": "staff123"})
    assert res.status_code == 200
    return res.json()["access_token"]
