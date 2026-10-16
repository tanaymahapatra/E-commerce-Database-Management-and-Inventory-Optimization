from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.recommendations import RecommendationListResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


# 1. Get recommendations for a product and warehouse
@router.get("", response_model=RecommendationListResponse)
def get_recommendations(
    product_id: int = Query(..., ge=1),
    warehouse_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):

    query = text("""
        SELECT
            forecast_date,
            predicted_demand,
            safety_stock,
            reorder_qty,
            status
        FROM recommendation
        WHERE product_id = :product_id
          AND warehouse_id = :warehouse_id
        ORDER BY forecast_date DESC
    """)

    result = (
        db.execute(query, {"product_id": product_id, "warehouse_id": warehouse_id})
        .mappings()
        .all()
    )

    recommendations = [dict(row) for row in result]

    return {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "total_records": len(recommendations),
        "recommendations": recommendations,
    }
