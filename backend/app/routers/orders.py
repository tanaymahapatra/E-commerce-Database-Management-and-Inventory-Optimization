from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.orders import (
    OrderDetailResponse,
    OrderListResponse,
    OrderStatusesResponse,
)

router = APIRouter(
    prefix="/orders",
    tags=["Orders"]
)


# 1. Get orders with pagination and optional filters
@router.get("", response_model=OrderListResponse)
def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    order_status: str | None = None,
    customer_id: str | None = None,
    db: Session = Depends(get_db)
):

    offset = (page - 1) * limit

    query = text("""
        SELECT
            order_id,
            order_date,
            customer_id,
            order_status,
            payment_method,
            payment_status
        FROM orders
        WHERE (:order_status IS NULL
               OR order_status = :order_status)
          AND (:customer_id IS NULL
               OR customer_id = :customer_id)
        ORDER BY order_id
        LIMIT :limit OFFSET :offset
    """)

    params = {
        "order_status": order_status,
        "customer_id": customer_id,
        "limit": limit,
        "offset": offset
    }

    result = db.execute(query, params).mappings().all()

    total = db.execute(
        text("""
            SELECT COUNT(*)
            FROM orders
            WHERE (:order_status IS NULL
                   OR order_status = :order_status)
              AND (:customer_id IS NULL
                   OR customer_id = :customer_id)
        """),
        {
            "order_status": order_status,
            "customer_id": customer_id
        }
    ).scalar_one()

    return {
        "page": page,
        "limit": limit,
        "total_orders": total,
        "orders": [dict(row) for row in result]
    }


# 2. Get all available order statuses
@router.get("/statuses", response_model=OrderStatusesResponse)
def get_order_statuses(db: Session = Depends(get_db)):

    query = text("""
        SELECT DISTINCT order_status
        FROM orders
        WHERE order_status IS NOT NULL
        ORDER BY order_status
    """)

    result = db.execute(query).scalars().all()

    return {"statuses": result}


# 3. Get an order with its purchased products
@router.get("/{order_id}", response_model=OrderDetailResponse)
def get_order(
    order_id: str,
    db: Session = Depends(get_db)
):

    # Retrieve order and customer information
    order = db.execute(
        text("""
            SELECT
                o.*,
                c.customer_name
            FROM orders o
            JOIN customers c
                ON o.customer_id = c.customer_id
            WHERE o.order_id = :order_id
        """),
        {"order_id": order_id}
    ).mappings().first()

    if order is None:
        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # Retrieve products purchased in the order
    query = text("""
        SELECT
            oi.product_id,
            p.product_name,
            oi.warehouse_id,
            w.warehouse_location,
            oi.quantity,
            oi.discount_percent,
            oi.total_price_usd
        FROM order_items oi
        JOIN product p
            ON oi.product_id = p.product_id
        JOIN warehouse w
            ON oi.warehouse_id = w.warehouse_id
        WHERE oi.order_id = :order_id
        ORDER BY oi.product_id, oi.warehouse_id
    """)

    result = db.execute(
        query,
        {"order_id": order_id}
    ).mappings().all()

    items = [dict(row) for row in result]

    return {
        "order": dict(order),
        "total_items": len(items),
        "items": items
    }
