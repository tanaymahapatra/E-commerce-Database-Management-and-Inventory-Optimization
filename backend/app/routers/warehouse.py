from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.warehouse import (
    WarehouseListResponse,
    WarehouseLocationsResponse,
    WarehouseResponse,
)

router = APIRouter(
    prefix="/warehouses",
    tags=["Warehouses"]
)


# 1. Get all warehouse locations
@router.get("/locations", response_model=WarehouseLocationsResponse)
def get_locations(db: Session = Depends(get_db)):

    query = text("""
        SELECT DISTINCT warehouse_location
        FROM warehouse
        ORDER BY warehouse_location
    """)

    locations = db.execute(query).scalars().all()

    return {"locations": locations}


# 2. Get warehouses with pagination
@router.get("", response_model=WarehouseListResponse)
def get_warehouses(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):

    offset = (page - 1) * limit

    query = text("""
        SELECT warehouse_id, warehouse_location
        FROM warehouse
        ORDER BY warehouse_id
        LIMIT :limit OFFSET :offset
    """)

    warehouses = db.execute(
        query,
        {"limit": limit, "offset": offset}
    ).mappings().all()

    total = db.execute(
        text("SELECT COUNT(*) FROM warehouse")
    ).scalar_one()

    return {
        "page": page,
        "limit": limit,
        "total_warehouses": total,
        "warehouses": [dict(row) for row in warehouses]
    }


# 3. Get a warehouse by ID
@router.get("/{warehouse_id}", response_model=WarehouseResponse)
def get_warehouse(
    warehouse_id: int,
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT warehouse_id, warehouse_location
        FROM warehouse
        WHERE warehouse_id = :warehouse_id
    """)

    warehouse = db.execute(
        query,
        {"warehouse_id": warehouse_id}
    ).mappings().first()

    if warehouse is None:
        raise HTTPException(
            status_code=404,
            detail="Warehouse not found"
        )

    return dict(warehouse)
