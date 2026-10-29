from datetime import datetime
from pydantic import BaseModel


class ProductStockDemand(BaseModel):
    product_id: int
    product_name: str
    stock_quantity: int
    predicted_demand: float | None = None
    forecast_date: datetime | None = None


class WarehouseStockDemandResponse(BaseModel):
    warehouse_id: int
    warehouse_location: str
    total_products: int
    total_stock: int
    products: list[ProductStockDemand]
