from pydantic import BaseModel, ConfigDict


class InventoryResponse(BaseModel):
    inventory_id: int
    product_id: int
    product_name: str
    warehouse_id: int
    warehouse_location: str
    stock_quantity: int

    # Illustrative Swagger example; not actual database data.
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "inventory_id": 1,
            "product_id": 1,
            "product_name": "Laptop",
            "warehouse_id": 1,
            "warehouse_location": "Guwahati",
            "stock_quantity": 250
        }
    })


class InventoryListResponse(BaseModel):
    page: int
    limit: int
    total_records: int
    inventory: list[InventoryResponse]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "page": 1,
            "limit": 10,
            "total_records": 2400,
            "inventory": [{
                "inventory_id": 1,
                "product_id": 1,
                "product_name": "Laptop",
                "warehouse_id": 1,
                "warehouse_location": "Guwahati",
                "stock_quantity": 250
            }]
        }
    })


class WarehouseInventoryProduct(BaseModel):
    inventory_id: int
    product_id: int
    product_name: str
    stock_quantity: int
    unit_price_usd: float | None


class WarehouseInventoryResponse(BaseModel):
    warehouse_id: int
    warehouse_location: str
    total_products: int
    total_stock: int
    products: list[WarehouseInventoryProduct]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "warehouse_id": 1,
            "warehouse_location": "Guwahati",
            "total_products": 1,
            "total_stock": 250,
            "products": [{
                "inventory_id": 1,
                "product_id": 1,
                "product_name": "Laptop",
                "stock_quantity": 250,
                "unit_price_usd": 899.99
            }]
        }
    })
