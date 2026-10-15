from pydantic import BaseModel, ConfigDict


class ProductResponse(BaseModel):
    product_id: int
    product_name: str
    category: str | None
    sub_category: str | None
    product_rating_avg: float | None
    product_reviews_count: int | None
    unit_price_usd: float | None

    # Illustrative Swagger example; not actual database data.
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "product_id": 1,
            "product_name": "Laptop",
            "category": "Electronics",
            "sub_category": "Computers",
            "product_rating_avg": 4.50,
            "product_reviews_count": 120,
            "unit_price_usd": 899.99
        }
    })


class ProductListResponse(BaseModel):
    page: int
    limit: int
    total_products: int
    products: list[ProductResponse]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "page": 1,
            "limit": 10,
            "total_products": 48,
            "products": [{
                "product_id": 1,
                "product_name": "Laptop",
                "category": "Electronics",
                "sub_category": "Computers",
                "product_rating_avg": 4.50,
                "product_reviews_count": 120,
                "unit_price_usd": 899.99
            }]
        }
    })


class ProductCategoriesResponse(BaseModel):
    categories: list[str]

    model_config = ConfigDict(json_schema_extra={
        "example": {"categories": ["Electronics", "Clothing"]}
    })
