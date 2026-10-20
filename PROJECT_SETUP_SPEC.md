# Project Specification: Product & Analytics Management System

**Stack:** Python 3.10+, FastAPI, Streamlit, MySQL 8.0+, SQLAlchemy 2.0, Pydantic v2, PyMySQL

---

## 1. Directory Tree

```text
app/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py
│   │   │   ├── audit.py
│   │   │   ├── auth.py
│   │   │   ├── products.py
│   │   │   └── users.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── security.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── audit.py
│   │   │   ├── product.py
│   │   │   ├── sale.py
│   │   │   └── user.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── analytics.py
│   │   │   ├── audit.py
│   │   │   ├── product.py
│   │   │   └── user.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── pages/
│   │   ├── 1_Products.py
│   │   ├── 2_Analytics.py
│   │   ├── 3_Profile.py
│   │   └── 4_Audit_Logs.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── api_client.py
│   ├── app.py
│   └── requirements.txt
└── schema.sql
```

---

## 2. Terminal Creation Commands

### Bash / Linux / macOS

```bash
mkdir -p app/backend/app/api app/backend/app/core app/backend/app/models app/backend/app/schemas app/frontend/pages app/frontend/utils

# Backend files
touch app/backend/app/__init__.py
touch app/backend/app/api/{__init__,analytics,audit,auth,products,users}.py
touch app/backend/app/core/{__init__,config,database,security}.py
touch app/backend/app/models/{__init__,audit,product,sale,user}.py
touch app/backend/app/schemas/{__init__,analytics,audit,product,user}.py
touch app/backend/app/main.py
touch app/backend/requirements.txt
touch app/backend/.env.example

# Frontend files
touch app/frontend/pages/{1_Products,2_Analytics,3_Profile,4_Audit_Logs}.py
touch app/frontend/utils/{__init__,api_client}.py
touch app/frontend/app.py
touch app/frontend/requirements.txt

# Database schema file
touch app/schema.sql
```

### Windows PowerShell

```powershell
New-Item -ItemType Directory -Force -Path `
  app/backend/app/api, `
  app/backend/app/core, `
  app/backend/app/models, `
  app/backend/app/schemas, `
  app/frontend/pages, `
  app/frontend/utils

New-Item -ItemType File -Force -Path `
  app/backend/app/__init__.py, `
  app/backend/app/api/__init__.py, `
  app/backend/app/api/analytics.py, `
  app/backend/app/api/audit.py, `
  app/backend/app/api/auth.py, `
  app/backend/app/api/products.py, `
  app/backend/app/api/users.py, `
  app/backend/app/core/__init__.py, `
  app/backend/app/core/config.py, `
  app/backend/app/core/database.py, `
  app/backend/app/core/security.py, `
  app/backend/app/models/__init__.py, `
  app/backend/app/models/audit.py, `
  app/backend/app/models/product.py, `
  app/backend/app/models/sale.py, `
  app/backend/app/models/user.py, `
  app/backend/app/schemas/__init__.py, `
  app/backend/app/schemas/analytics.py, `
  app/backend/app/schemas/audit.py, `
  app/backend/app/schemas/product.py, `
  app/backend/app/schemas/user.py, `
  app/backend/app/main.py, `
  app/backend/requirements.txt, `
  app/backend/.env.example

New-Item -ItemType File -Force -Path `
  app/frontend/pages/1_Products.py, `
  app/frontend/pages/2_Analytics.py, `
  app/frontend/pages/3_Profile.py, `
  app/frontend/pages/4_Audit_Logs.py, `
  app/frontend/utils/__init__.py, `
  app/frontend/utils/api_client.py, `
  app/frontend/app.py, `
  app/frontend/requirements.txt, `
  app/schema.sql
```

---

## 3. Database Initialization (`app/schema.sql`)

```sql
CREATE DATABASE IF NOT EXISTS store_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE store_db;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'staff') NOT NULL DEFAULT 'staff',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_role (role),
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    description TEXT,
    active_status BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_products_category (category),
    INDEX idx_products_active (active_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT NOT NULL,
    user_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_sales_date (sale_date),
    INDEX idx_sales_product (product_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    module VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_audit_module (module),
    INDEX idx_audit_created (created_at)
) ENGINE=InnoDB;
```

---

## 4. Dependencies

### `app/backend/requirements.txt`

```text
fastapi>=0.110.0
uvicorn[standard]>=0.28.0
sqlalchemy>=2.0.28
pymysql>=1.1.0
cryptography>=42.0.5
pydantic>=2.6.4
pydantic-settings>=2.2.1
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.9
```

### `app/frontend/requirements.txt`

```text
streamlit>=1.32.0
requests>=2.31.0
pandas>=2.2.1
plotly>=5.20.0
```

---

## 5. Environment Configuration

### `app/backend/.env.example`

```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=store_db
SECRET_KEY=generate_a_secure_random_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## 6. API Endpoint Contract

| Module | HTTP Method | Endpoint | Description |
| --- | --- | --- | --- |
| **Auth** | `POST` | `/auth/token` | User login returning Bearer JWT |
| **Products** | `GET` | `/products` | List products with query params (`category`, `active_status`, `search`) |
|  | `GET` | `/products/{product_id}` | Retrieve specific product details |
|  | `POST` | `/products` | Create product |
|  | `PUT` | `/products/{product_id}` | Update product details |
|  | `DELETE` | `/products/{product_id}` | Soft delete (`active_status=False`) |
| **Analytics** | `GET` | `/analytics/summary` | Overall KPI summary (total sales, revenue, orders) |
|  | `GET` | `/analytics/monthly` | Monthly sales aggregations via MySQL `DATE_FORMAT` |
|  | `GET` | `/analytics/products` | Top and lower performing products by revenue/volume |
|  | `GET` | `/analytics/categories` | Revenue and volume grouped by category |
| **Users** | `GET` | `/profile` | Current authenticated user profile |
|  | `PUT` | `/profile` | Update profile information or change password |
|  | `GET` | `/users` | List all users (Admin only) |
|  | `GET` | `/users/{user_id}` | Get user details (Admin only) |
|  | `POST` | `/users` | Create user (Admin only) |
|  | `PUT` | `/users/{user_id}` | Update user role / status (Admin only) |
| **Audit** | `GET` | `/audit-logs` | Filter audit logs by user, module, date range |
|  | `GET` | `/audit-logs/{log_id}` | Get specific audit entry details |

---

## 7. Streamlit App Layout

* `app.py`: Authentication gate, login form, sets `st.session_state["token"]` and `st.session_state["user"]`.
* `pages/1_Products.py`: View products catalog, category dropdown filter, search input, add product modal/expander, edit and deactivate buttons.
* `pages/2_Analytics.py`: Revenue overview cards, monthly sales line chart, top/bottom products bar chart, category breakdown pie/bar chart, price vs. quantity scatter plot.
* `pages/3_Profile.py`: User profile details, change password form, admin user management table.
* `pages/4_Audit_Logs.py`: Chronological activity history with user, module, and date filters.

---

## 8. How to Save This Directly to an `.md` File

Run this one-liner in your terminal to save the specification directly as `PROJECT_SETUP_SPEC.md`:

```bash
cat << 'EOF' > PROJECT_SETUP_SPEC.md
# Paste the content of the specification here
EOF
```
