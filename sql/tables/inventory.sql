CREATE TABLE inventory (
    inventory_id INT,

    product_id INT NOT NULL,

    warehouse_id INT NOT NULL,

    stock_quantity INT NOT NULL
        CHECK (stock_quantity >=0),


    PRIMARY KEY (inventory_id),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES product(product_id)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

    CONSTRAINT fk_inventory_warehouse
        FOREIGN KEY (warehouse_id)
        REFERENCES warehouse(warehouse_id)

    ON DELETE RESTRICT
    ON UPDATE CASCADE,

    CONSTRAINT uq_inventory_product_warehouse
    UNIQUE (product_id, warehouse_id)
);