from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from pathlib import Path
from ..database import get_db
from ..schemas.recommendations import RecommendationListResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

SQL_FILE = (Path(__file__).resolve().parents[3] /"sql"/"queries"/"get_recommendation.sql")

with SQL_FILE.open("r", encoding="utf-8") as file:
    GET_RECOMMENDATION_QUERY = text(file.read())

# 1. Get recommendations for a product and warehouse
@router.get("", response_model=RecommendationListResponse)
def get_recommendations(
    product_id: int = Query(..., ge=1),
    warehouse_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):

    result = (
        db.execute(GET_RECOMMENDATION_QUERY, {"product_id": product_id, "warehouse_id": warehouse_id})
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
