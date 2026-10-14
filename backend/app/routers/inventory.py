from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.inventory import (
    InventoryListResponse,
    InventoryResponse,
    WarehouseInventoryResponse,
)

router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


# 1. Get inventory with pagination and optional filters
@router.get("", response_model=InventoryListResponse)
def get_inventory(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    warehouse_id: int | None = None,
    product_id: int | None = None,
    db: Session = Depends(get_db)
):

    offset = (page - 1) * limit

    query = text("""
        SELECT
            i.inventory_id,
            i.product_id,
            p.product_name,
            i.warehouse_id,
            w.warehouse_location,
            i.stock_quantity
        FROM inventory i
        JOIN product p
            ON i.product_id = p.product_id
        JOIN warehouse w
            ON i.warehouse_id = w.warehouse_id
        WHERE (:warehouse_id IS NULL
               OR i.warehouse_id = :warehouse_id)
          AND (:product_id IS NULL
               OR i.product_id = :product_id)
        ORDER BY i.inventory_id
        LIMIT :limit OFFSET :offset
    """)

    params = {
        "warehouse_id": warehouse_id,
        "product_id": product_id,
        "limit": limit,
        "offset": offset
    }

    result = db.execute(query, params).mappings().all()

    total = db.execute(
        text("""
            SELECT COUNT(*)
            FROM inventory
            WHERE (:warehouse_id IS NULL
                   OR warehouse_id = :warehouse_id)
              AND (:product_id IS NULL
                   OR product_id = :product_id)
        """),
        {
            "warehouse_id": warehouse_id,
            "product_id": product_id
        }
    ).scalar_one()

    return {
        "page": page,
        "limit": limit,
        "total_records": total,
        "inventory": [dict(row) for row in result]
    }


# 2. Get inventory for a particular warehouse
@router.get("/warehouse/{warehouse_id}", response_model=WarehouseInventoryResponse)
def get_warehouse_inventory(
    warehouse_id: int,
    db: Session = Depends(get_db)
):

    # Verify that warehouse exists
    warehouse = db.execute(
        text("""
            SELECT warehouse_id, warehouse_location
            FROM warehouse
            WHERE warehouse_id = :warehouse_id
        """),
        {"warehouse_id": warehouse_id}
    ).mappings().first()

    if warehouse is None:
        raise HTTPException(
            status_code=404,
            detail="Warehouse not found"
        )

    query = text("""
        SELECT
            i.inventory_id,
            i.product_id,
            p.product_name,
            i.stock_quantity,
            p.unit_price_usd
        FROM inventory i
        JOIN product p
            ON i.product_id = p.product_id
        WHERE i.warehouse_id = :warehouse_id
        ORDER BY p.product_name
    """)

    result = db.execute(
        query,
        {"warehouse_id": warehouse_id}
    ).mappings().all()

    products = [dict(row) for row in result]

    total_stock = sum(
        row["stock_quantity"] for row in products
    )

    return {
        "warehouse_id": warehouse_id,
        "warehouse_location": warehouse["warehouse_location"],
        "total_products": len(products),
        "total_stock": total_stock,
        "products": products
    }


# 3. Get an inventory record by ID
@router.get("/{inventory_id}", response_model=InventoryResponse)
def get_inventory_by_id(
    inventory_id: int,
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT
            i.inventory_id,
            i.product_id,
            p.product_name,
            i.warehouse_id,
            w.warehouse_location,
            i.stock_quantity
        FROM inventory i
        JOIN product p
            ON i.product_id = p.product_id
        JOIN warehouse w
            ON i.warehouse_id = w.warehouse_id
        WHERE i.inventory_id = :inventory_id
    """)

    result = db.execute(
        query,
        {"inventory_id": inventory_id}
    ).mappings().first()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Inventory record not found"
        )

    return dict(result)
