from pydantic import BaseModel, ConfigDict


class SalesSummaryResponse(BaseModel):
    total_orders: int
    total_units_sold: int
    total_revenue_usd: float
    total_profit_usd: float

    # Illustrative Swagger example; not actual database data.
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "total_orders": 100,
            "total_units_sold": 150,
            "total_revenue_usd": 45000.00,
            "total_profit_usd": 8500.00
        }
    })


class MonthlySalesItem(BaseModel):
    month: str
    total_orders: int
    total_units_sold: int
    total_revenue_usd: float
    total_profit_usd: float


class MonthlySalesResponse(BaseModel):
    monthly_sales: list[MonthlySalesItem]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "monthly_sales": [{
                "month": "2025-03",
                "total_orders": 100,
                "total_units_sold": 150,
                "total_revenue_usd": 45000.00,
                "total_profit_usd": 8500.00
            }]
        }
    })


class TopProductItem(BaseModel):
    product_id: int
    product_name: str
    category: str | None
    total_units_sold: int
    total_revenue_usd: float
    total_profit_usd: float


class TopProductsResponse(BaseModel):
    top_products: list[TopProductItem]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "top_products": [{
                "product_id": 1,
                "product_name": "Laptop",
                "category": "Electronics",
                "total_units_sold": 40,
                "total_revenue_usd": 35999.60,
                "total_profit_usd": 6000.00
            }]
        }
    })


class WarehousePerformanceItem(BaseModel):
    warehouse_id: int
    warehouse_location: str
    total_orders: int
    total_units_sold: int
    total_revenue_usd: float
    total_profit_usd: float


class WarehousePerformanceResponse(BaseModel):
    warehouses: list[WarehousePerformanceItem]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "warehouses": [{
                "warehouse_id": 1,
                "warehouse_location": "Guwahati",
                "total_orders": 100,
                "total_units_sold": 150,
                "total_revenue_usd": 45000.00,
                "total_profit_usd": 8500.00
            }]
        }
    })


class CategoryPerformanceItem(BaseModel):
    category: str
    total_units_sold: int
    total_revenue_usd: float
    total_profit_usd: float


class CategoryPerformanceResponse(BaseModel):
    categories: list[CategoryPerformanceItem]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "categories": [{
                "category": "Electronics",
                "total_units_sold": 75,
                "total_revenue_usd": 30000.00,
                "total_profit_usd": 5500.00
            }]
        }
    })
