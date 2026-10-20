CREATE DATABASE IF NOT EXISTS store_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE store_db;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(120) NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'staff', 'analyst') NOT NULL DEFAULT 'staff',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    failed_login_attempts INT NOT NULL DEFAULT 0,
    locked_until DATETIME NULL,
    last_login_at DATETIME NULL,
    token_version INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_role (role),
    INDEX idx_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS auth_sessions (
    auth_session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_expires_at DATETIME NOT NULL,
    logout_at DATETIME NULL,
    logout_reason VARCHAR(20) NULL,
    CONSTRAINT fk_auth_sessions_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_auth_sessions_user_login (user_id, login_at),
    INDEX idx_auth_sessions_logout (logout_at)
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
    INDEX idx_sales_product (product_id),
    INDEX idx_sales_user (user_id)
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

CREATE TABLE IF NOT EXISTS model_runs (
    model_run_id INT AUTO_INCREMENT PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    prediction_target VARCHAR(64) NOT NULL,
    training_records INT NOT NULL DEFAULT 0,
    evaluation_records INT NOT NULL DEFAULT 0,
    mae DOUBLE NULL,
    rmse DOUBLE NULL,
    r2 DOUBLE NULL,
    trained_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    artifact_path VARCHAR(500) NULL,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    training_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT NULL,
    UNIQUE KEY uq_model_runs_name_version (model_name, model_version),
    INDEX idx_model_runs_active_trained (is_active, trained_at),
    INDEX idx_model_runs_status (training_status),
    INDEX idx_model_runs_trained (trained_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS prediction_history (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    model_run_id INT NOT NULL,
    product_id INT NULL,
    forecast_date DATE NOT NULL,
    horizon_days INT NOT NULL,
    predicted_quantity DECIMAL(14, 4) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(64) NOT NULL,
    predicted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    actual_quantity DECIMAL(14, 4) NULL,
    CONSTRAINT fk_prediction_model_run FOREIGN KEY (model_run_id) REFERENCES model_runs(model_run_id) ON DELETE RESTRICT,
    CONSTRAINT fk_prediction_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL,
    CONSTRAINT fk_prediction_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE RESTRICT,
    INDEX idx_prediction_product_date (product_id, forecast_date),
    INDEX idx_prediction_user_time (user_id, predicted_at),
    INDEX idx_prediction_model_version (model_version),
    INDEX idx_prediction_time (predicted_at)
) ENGINE=InnoDB;
