CREATE TABLE product (
    product_id INT,

    product_name VARCHAR(150) NOT NULL,

    category VARCHAR(50),

    sub_category VARCHAR(50),

    brand VARCHAR(100),

    product_rating_avg DECIMAL(3,2)
        CHECK (product_rating_avg BETWEEN 0 AND 5),

    product_reviews_count INT DEFAULT 0
        CHECK (product_reviews_count >= 0),

    unit_price_usd DECIMAL(10,2)
        CHECK (unit_price_usd >= 0),


    PRIMARY KEY (product_id)
);