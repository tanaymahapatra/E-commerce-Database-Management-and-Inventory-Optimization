CREATE TABLE IF NOT EXISTS user_warehouse_access (
    user_id INT NOT NULL PRIMARY KEY,
    warehouse_id INT NOT NULL UNIQUE,

    CONSTRAINT chk_matching_ids
        CHECK (user_id = warehouse_id),

    FOREIGN KEY (user_id)
        REFERENCES app_users(user_id)
        ON DELETE CASCADE,

    FOREIGN KEY (warehouse_id)
        REFERENCES warehouse(warehouse_id)
        ON DELETE CASCADE
);
