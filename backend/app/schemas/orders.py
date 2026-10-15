from datetime import datetime
from pydantic import BaseModel, ConfigDict


class OrderListItem(BaseModel):
    order_id: str
    order_date: datetime
    customer_id: str
    order_status: str | None
    payment_method: str | None
    payment_status: str | None


class OrderListResponse(BaseModel):
    page: int
    limit: int
    total_orders: int
    orders: list[OrderListItem]

    # Illustrative Swagger example; not actual database data.
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "page": 1,
            "limit": 10,
            "total_orders": 749817,
            "orders": [{
                "order_id": "ORD-001",
                "order_date": "2025-03-01T10:30:00",
                "customer_id": "CUS-001",
                "order_status": "Delivered",
                "payment_method": "Card",
                "payment_status": "Paid"
            }]
        }
    })


class OrderStatusesResponse(BaseModel):
    statuses: list[str]

    model_config = ConfigDict(json_schema_extra={
        "example": {"statuses": ["Delivered", "Pending"]}
    })


class OrderDetail(BaseModel):
    order_id: str
    order_date: datetime
    is_weekend: int
    order_status: str | None
    payment_method: str | None
    payment_status: str | None
    installment_plan: str | None
    device_type: str | None
    customer_id: str
    customer_name: str


class OrderItemResponse(BaseModel):
    product_id: int
    product_name: str
    warehouse_id: int
    warehouse_location: str
    quantity: int
    discount_percent: int | None
    total_price_usd: float | None


class OrderDetailResponse(BaseModel):
    order: OrderDetail
    total_items: int
    items: list[OrderItemResponse]

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "order": {
                "order_id": "ORD-001",
                "order_date": "2025-03-01T10:30:00",
                "is_weekend": 1,
                "order_status": "Delivered",
                "payment_method": "Card",
                "payment_status": "Paid",
                "installment_plan": "No",
                "device_type": "Mobile",
                "customer_id": "CUS-001",
                "customer_name": "Example Customer"
            },
            "total_items": 1,
            "items": [{
                "product_id": 1,
                "product_name": "Laptop",
                "warehouse_id": 1,
                "warehouse_location": "Guwahati",
                "quantity": 1,
                "discount_percent": 10,
                "total_price_usd": 809.99
            }]
        }
    })
