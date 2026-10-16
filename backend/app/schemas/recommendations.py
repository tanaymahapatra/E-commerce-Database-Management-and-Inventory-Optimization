from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class RecommendationResponse(BaseModel):
    forecast_date: datetime
    predicted_demand: float
    safety_stock: int
    reorder_qty: int
    status: Literal["OK", "REORDER_NOW", "CRITICAL", "OVERSHOOT"]


class RecommendationListResponse(BaseModel):
    product_id: int
    warehouse_id: int
    total_records: int
    recommendations: list[RecommendationResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "product_id": 1,
                "warehouse_id": 5,
                "total_records": 1,
                "recommendations": [
                    {
                        "forecast_date": "2026-10-17T00:00:00",
                        "predicted_demand": 125.50,
                        "safety_stock": 30,
                        "reorder_qty": 80,
                        "status": "REORDER_NOW",
                    }
                ],
            }
        }
    )
