-- Store one row per authenticated session so login and logout times can be paired.
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
