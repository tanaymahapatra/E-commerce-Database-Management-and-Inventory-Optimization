from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.products import (
    ProductCategoriesResponse,
    ProductListResponse,
    ProductResponse,
)

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# 1. Get all product categories
@router.get("/categories", response_model=ProductCategoriesResponse)
def get_categories(db: Session = Depends(get_db)):

    query = text("""
        SELECT DISTINCT category
        FROM product
        WHERE category IS NOT NULL
        ORDER BY category
    """)

    result = db.execute(query).scalars().all()

    return {"categories": result}


# 2. Get products with pagination and optional category filter
@router.get("", response_model=ProductListResponse)
def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    category: str | None = None,
    db: Session = Depends(get_db)
):

    offset = (page - 1) * limit

    query = text("""
        SELECT *
        FROM product
        WHERE (:category IS NULL OR category = :category)
        ORDER BY product_id
        LIMIT :limit OFFSET :offset
    """)

    result = db.execute(
        query,
        {
            "category": category,
            "limit": limit,
            "offset": offset
        }
    ).mappings().all()

    total = db.execute(
        text("""
            SELECT COUNT(*)
            FROM product
            WHERE (:category IS NULL OR category = :category)
        """),
        {"category": category}
    ).scalar_one()

    return {
        "page": page,
        "limit": limit,
        "total_products": total,
        "products": [dict(row) for row in result]
    }


# 3. Get one product by ID
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT *
        FROM product
        WHERE product_id = :product_id
    """)

    result = db.execute(
        query,
        {"product_id": product_id}
    ).mappings().first()

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return dict(result)
