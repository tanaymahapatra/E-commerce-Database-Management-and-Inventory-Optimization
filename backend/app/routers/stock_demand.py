from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import get_current_user, check_warehouse_access
from ..schemas.stock_demand import WarehouseStockDemandResponse

router = APIRouter(prefix="/stock-demand", tags=["Stock and Demand"])


# 1. Get product-wise stock and demand for a warehouse
@router.get("/{warehouse_id}", response_model=WarehouseStockDemandResponse)
def get_stock_demand(
    warehouse_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):

    # Check warehouse permission
    check_warehouse_access(db, user, warehouse_id)

    # Get warehouse information
    warehouse = (
        db.execute(
            text("""
            SELECT warehouse_id, warehouse_location
            FROM warehouse
            WHERE warehouse_id = :warehouse_id
        """),
            {"warehouse_id": warehouse_id},
        )
        .mappings()
        .first()
    )

    if warehouse is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    # Get products, stock and latest forecast
    query = text("""
        SELECT
            i.product_id,
            p.product_name,
            i.stock_quantity,
            r.predicted_demand,
            r.forecast_date

        FROM inventory i

        JOIN product p
            ON i.product_id = p.product_id

        LEFT JOIN recommendation r
            ON r.product_id = i.product_id
            AND r.warehouse_id = i.warehouse_id
            AND r.forecast_date = (
                SELECT MAX(r2.forecast_date)
                FROM recommendation r2
                WHERE r2.product_id = i.product_id
                  AND r2.warehouse_id = i.warehouse_id
            )

        WHERE i.warehouse_id = :warehouse_id
        ORDER BY p.product_name, i.product_id
    """)

    result = db.execute(query, {"warehouse_id": warehouse_id}).mappings().all()

    products = [dict(row) for row in result]

    total_stock = sum(row["stock_quantity"] for row in products)

    return {
        "warehouse_id": warehouse_id,
        "warehouse_location": warehouse["warehouse_location"],
        "total_products": len(products),
        "total_stock": total_stock,
        "products": products,
    }
