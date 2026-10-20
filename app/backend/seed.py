import sys
import os
from datetime import datetime, timedelta
import random

# Add parent directory to path so imports work cleanly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.product import Product
from app.models.sale import Sale
from app.models.audit import AuditLog


def seed_database():
    print("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Seed Users
        users_data = [
            {"username": "admin", "email": "admin@store.com", "password": "adminpassword123", "role": UserRole.ADMIN},
            {"username": "manager_alex", "email": "alex.manager@store.com", "password": "managerpassword123", "role": UserRole.MANAGER},
            {"username": "staff_emma", "email": "emma.staff@store.com", "password": "staffpassword123", "role": UserRole.STAFF},
        ]

        created_users = []
        for u in users_data:
            existing = db.query(User).filter(User.username == u["username"]).first()
            if not existing:
                user = User(
                    username=u["username"],
                    email=u["email"],
                    hashed_password=get_password_hash(u["password"]),
                    role=u["role"],
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                created_users.append(user)
                print(f"Created user: {user.username} ({user.role})")
            else:
                created_users.append(existing)

        admin_user = created_users[0]

        # 2. Seed Products
        products_data = [
            {"product_name": "UltraHD 4K Curved Monitor 34-inch", "category": "Electronics", "base_price": 549.99, "description": "34-inch ultra-wide 144Hz curved monitor for professionals and gamers.", "active_status": True},
            {"product_name": "Noise Cancelling Wireless Headphones", "category": "Audio", "base_price": 199.99, "description": "Over-ear headphones with active noise cancellation and 40h battery.", "active_status": True},
            {"product_name": "Mechanical RGB Gaming Keyboard", "category": "Accessories", "base_price": 89.99, "description": "Custom mechanical tactile switches with RGB per-key backlighting.", "active_status": True},
            {"product_name": "Ergonomic Mesh Office Chair", "category": "Furniture", "base_price": 289.00, "description": "Breathable high-back ergonomic chair with adjustable lumbar support.", "active_status": True},
            {"product_name": "Standing Desk Converter Pro", "category": "Furniture", "base_price": 169.50, "description": "Height adjustable dual-tier tabletop standing desk converter.", "active_status": True},
            {"product_name": "USB-C Multiport Hub 8-in-1", "category": "Accessories", "base_price": 45.00, "description": "Compact hub with 4K HDMI, Gigabit Ethernet, SD card, 100W PD.", "active_status": True},
            {"product_name": "Precision Wireless Mouse", "category": "Accessories", "base_price": 49.99, "description": "Ergonomic wireless mouse with hyperscroll and multi-device pairing.", "active_status": True},
            {"product_name": "Smart LED Desk Lamp with Wireless Charger", "category": "Lighting", "base_price": 39.99, "description": "Adjustable color temperature lamp with built-in 10W fast charger.", "active_status": True},
            {"product_name": "Compact Espresso & Coffee Machine", "category": "Kitchen", "base_price": 229.00, "description": "15-bar pressure Italian espresso pump with steam wand.", "active_status": True},
            {"product_name": "Insulated Stainless Steel Tumbler 750ml", "category": "Kitchen", "base_price": 24.50, "description": "Double-wall vacuum insulated travel mug keeps drinks cold 24h.", "active_status": True},
            {"product_name": "Legacy USB 2.0 Flash Drive 8GB", "category": "Accessories", "base_price": 6.99, "description": "Older discontinued storage drive.", "active_status": False},
        ]

        saved_products = []
        for p in products_data:
            existing = db.query(Product).filter(Product.product_name == p["product_name"]).first()
            if not existing:
                prod = Product(
                    product_name=p["product_name"],
                    category=p["category"],
                    base_price=p["base_price"],
                    description=p["description"],
                    active_status=p["active_status"]
                )
                db.add(prod)
                db.commit()
                db.refresh(prod)
                saved_products.append(prod)
                print(f"Created product: {prod.product_name}")
            else:
                saved_products.append(existing)

        # 3. Seed Sales if empty
        sale_count = db.query(Sale).count()
        if sale_count == 0:
            active_prods = [p for p in saved_products if p.active_status]
            if active_prods and created_users:
                print("Seeding sales records...")
                now = datetime.now()

                for i in range(120):
                    # Generate dates over last 6 months
                    days_ago = random.randint(0, 180)
                    sale_time = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))
                    
                    prod = random.choice(active_prods)
                    user = random.choice(created_users)
                    qty = random.choices([1, 2, 3, 4, 5, 8], weights=[50, 25, 12, 8, 3, 2])[0]
                    unit_price = float(prod.base_price)
                    discount = round(unit_price * qty * random.choice([0.0, 0.05, 0.10, 0.15]), 2)
                    total = round((unit_price * qty) - discount, 2)

                    sale = Sale(
                        product_id=prod.product_id,
                        user_id=user.user_id,
                        quantity=qty,
                        unit_price=unit_price,
                        discount_amount=discount,
                        total_amount=total,
                        sale_date=sale_time
                    )
                    db.add(sale)

                db.commit()
                print("Seeded 120 sales records.")

        # 4. Seed Audit Logs
        log_count = db.query(AuditLog).count()
        if log_count == 0:
            print("Seeding initial audit logs...")
            sample_logs = [
                {"user_id": admin_user.user_id, "action": "INITIALIZE_SYSTEM", "module": "SYSTEM", "description": "Initial system setup and database seeding performed."},
                {"user_id": admin_user.user_id, "action": "CREATE_USER", "module": "USERS", "description": "Admin created manager and staff accounts."},
                {"user_id": admin_user.user_id, "action": "CREATE_PRODUCT", "module": "PRODUCTS", "description": "Populated initial inventory items."},
            ]
            for l in sample_logs:
                log = AuditLog(
                    user_id=l["user_id"],
                    action=l["action"],
                    module=l["module"],
                    description=l["description"]
                )
                db.add(log)
            db.commit()
            print("Seeded initial audit logs.")

        print("\n=== Seeding Completed Successfully! ===")
        print("Default credentials:")
        print("  - Admin:   username: 'admin'        | password: 'adminpassword123'")
        print("  - Manager: username: 'manager_alex' | password: 'managerpassword123'")
        print("  - Staff:   username: 'staff_emma'   | password: 'staffpassword123'")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
