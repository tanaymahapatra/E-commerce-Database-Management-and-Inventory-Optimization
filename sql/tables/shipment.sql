CREATE TABLE shipment (
    order_id VARCHAR(20),

    shipping_method VARCHAR(50)
        CHECK (shipping_method IN
            ('Economy', 'Next Day', 'Express', 'Standard')),

    shipping_cost_usd DECIMAL(10,2)
        CHECK (shipping_cost_usd >= 0),

    delivery_days INT
        CHECK (delivery_days >= 0),

    shipping_country VARCHAR(100),


    delivery_status VARCHAR(30)
        CHECK (delivery_status IN
            ('In Transit', 'Delivered', 'Failed', 'Pending')),

    PRIMARY KEY(order_id),

    CONSTRAINT fk_shipment_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE
);