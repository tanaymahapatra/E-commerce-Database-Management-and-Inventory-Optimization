from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.analytics import (
    CategoryPerformanceResponse,
    MonthlySalesResponse,
    SalesSummaryResponse,
    TopProductsResponse,
    WarehousePerformanceResponse,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


# 1. Get overall sales summary
@router.get("/summary", response_model=SalesSummaryResponse)
def get_sales_summary(db: Session = Depends(get_db)):

    total_orders = db.execute(
        text("SELECT COUNT(*) FROM orders")
    ).scalar_one()

    query = text("""
        SELECT
            COALESCE(SUM(quantity), 0) AS total_units_sold,
            COALESCE(SUM(total_price_usd), 0) AS total_revenue_usd,
            COALESCE(SUM(profit_usd), 0) AS total_profit_usd
        FROM order_items
    """)

    result = db.execute(query).mappings().first()

    return {
        "total_orders": total_orders,
        **dict(result)
    }


# 2. Get monthly sales trends
@router.get("/monthly-sales", response_model=MonthlySalesResponse)
def get_monthly_sales(db: Session = Depends(get_db)):

    query = text("""
        SELECT
            DATE_FORMAT(o.order_date, '%Y-%m') AS month,
            COUNT(DISTINCT o.order_id) AS total_orders,
            COALESCE(SUM(oi.quantity), 0) AS total_units_sold,
            COALESCE(SUM(oi.total_price_usd), 0) AS total_revenue_usd,
            COALESCE(SUM(oi.profit_usd), 0) AS total_profit_usd
        FROM orders o
        LEFT JOIN order_items oi
            ON o.order_id = oi.order_id
        GROUP BY DATE_FORMAT(o.order_date, '%Y-%m')
        ORDER BY month
    """)

    result = db.execute(query).mappings().all()

    return {
        "monthly_sales": [dict(row) for row in result]
    }


# 3. Get top-selling products
@router.get("/top-products", response_model=TopProductsResponse)
def get_top_products(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT
            p.product_id,
            p.product_name,
            p.category,
            SUM(oi.quantity) AS total_units_sold,
            COALESCE(SUM(oi.total_price_usd), 0) AS total_revenue_usd,
            COALESCE(SUM(oi.profit_usd), 0) AS total_profit_usd
        FROM order_items oi
        JOIN product p
            ON oi.product_id = p.product_id
        GROUP BY
            p.product_id,
            p.product_name,
            p.category
        ORDER BY total_units_sold DESC, p.product_id
        LIMIT :limit
    """)

    result = db.execute(
        query,
        {"limit": limit}
    ).mappings().all()

    return {
        "top_products": [dict(row) for row in result]
    }


# 4. Get warehouse sales performance
@router.get("/warehouses", response_model=WarehousePerformanceResponse)
def get_warehouse_performance(
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT
            w.warehouse_id,
            w.warehouse_location,
            COUNT(DISTINCT oi.order_id) AS total_orders,
            SUM(oi.quantity) AS total_units_sold,
            COALESCE(SUM(oi.total_price_usd), 0) AS total_revenue_usd,
            COALESCE(SUM(oi.profit_usd), 0) AS total_profit_usd
        FROM order_items oi
        JOIN warehouse w
            ON oi.warehouse_id = w.warehouse_id
        GROUP BY
            w.warehouse_id,
            w.warehouse_location
        ORDER BY total_revenue_usd DESC, w.warehouse_id
    """)

    result = db.execute(query).mappings().all()

    return {
        "warehouses": [dict(row) for row in result]
    }


# 5. Get sales performance by product category
@router.get("/categories", response_model=CategoryPerformanceResponse)
def get_category_performance(
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT
            COALESCE(p.category, 'Uncategorized') AS category,
            SUM(oi.quantity) AS total_units_sold,
            COALESCE(SUM(oi.total_price_usd), 0) AS total_revenue_usd,
            COALESCE(SUM(oi.profit_usd), 0) AS total_profit_usd
        FROM order_items oi
        JOIN product p
            ON oi.product_id = p.product_id
        GROUP BY COALESCE(p.category, 'Uncategorized')
        ORDER BY total_revenue_usd DESC, category
    """)

    result = db.execute(query).mappings().all()

    return {
        "categories": [dict(row) for row in result]
    }
