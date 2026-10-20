-- Additive forecasting tables. Existing users, products, sales, and IDs are unchanged.
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