-- Apply once to an existing MySQL database before deploying Phase 1.
-- Existing products, sales, and their product IDs are preserved.
ALTER TABLE users
    MODIFY COLUMN role ENUM('admin', 'manager', 'staff', 'analyst') NOT NULL DEFAULT 'staff',
    ADD COLUMN failed_login_attempts INT NOT NULL DEFAULT 0,
    ADD COLUMN locked_until DATETIME NULL,
    ADD COLUMN last_login_at DATETIME NULL,
    ADD COLUMN token_version INT NOT NULL DEFAULT 0;

CREATE INDEX idx_sales_user ON sales (user_id);