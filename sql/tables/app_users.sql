CREATE TABLE IF NOT EXISTS app_users (
    user_id INT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'manager', 'analyst') NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);
