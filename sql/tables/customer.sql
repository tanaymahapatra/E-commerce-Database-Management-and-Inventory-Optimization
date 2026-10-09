CREATE TABLE customers (
    customer_id VARCHAR(20),
    customer_name VARCHAR(100) NOT NULL,

    gender VARCHAR(20)
        CHECK (gender IN ('Male', 'Female')),


    age INT
        CHECK (age >= 14 AND age <= 120),

    customer_segment VARCHAR(50)
        CHECK (customer_segment IN ('Regular', 'VIP', 'Premium')),

    country VARCHAR(50),
    city VARCHAR(100),

    customer_loyalty_score DECIMAL(5,2)
        CHECK (customer_loyalty_score BETWEEN 0 AND 100),

    --total_orders_by_customer INT DEFAULT 0
        --CHECK (total_orders_by_customer >= 0),

    account_creation_date DATE,
    PRIMARY KEY (customer_id)
);