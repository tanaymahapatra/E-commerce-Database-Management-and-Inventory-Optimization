CREATE TABLE order (
    order_id VARCHAR(20),
    order_date DATETIME NOT NULL,

    is_weekend BOOLEAN NOT NULL,

    order_status VARCHAR(30)
        CHECK (order_status IN
            ('Completed', 'Returned', 'Pending', 'Cancelled', 'Processing')),

    payment_method VARCHAR(30)
        CHECK (payment_method IN
            ('Apple Pay', 'Bank Transfer', 'Credit Card', 'PayPal', 'Debit Card')),

    payment_status VARCHAR(30)
        CHECK (payment_status IN
            ('Paid', 'Pending', 'Failed')),

    installment_plan VARCHAR(3)
        CHECK (installment_plan IN ('Yes', 'No')),

    device_type VARCHAR(30)
        CHECK (device_type IN ('Mobile', 'Desktop', 'Tablet')),

    customer_id VARCHAR(20) NOT NULL,

    PRIMARY KEY (order_id),

    CONSTRAINT fk_order_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE
);